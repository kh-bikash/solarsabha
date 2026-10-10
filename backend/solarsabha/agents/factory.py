"""Build the model and the agents (Strands Agents SDK, strands-agents 1.58).

MODEL_PROVIDER picks the model behind every agent; the agents, tools, hooks and prompts are the same either way:
- gemini (default): Google Gemini. Key from GEMINI_API_KEY (local .env) or the encrypted SSM parameter named by
  GEMINI_KEY_PARAM (on AWS). GEMINI_MODEL_ID is a comma-separated fallback chain (quota errors move to the next model).
  A backup provider (OpenAI-compatible) joins the end of the chain for the text agents (review, DISCOM replies,
  letters) when its key is set: BazaarLink (BAZAARLINK_API_KEY / SSM BAZAARLINK_KEY_PARAM, models BAZAARLINK_MODEL_ID).
  It is not used for reading PDFs or photos, which stays on Gemini with the plain-code reader behind it.
- bedrock: Amazon Bedrock. Model or inference profile: BEDROCK_MODEL_ID.
Run `python scripts/smoke_live.py` to check the live path."""
import contextvars
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from contextvars import ContextVar
from functools import lru_cache
from strands import Agent, ToolContext, tool
from strands.handlers.callback_handler import null_callback_handler
from strands.tools.executors import SequentialToolExecutor
from ..trace import Trace, TraceHooks
from ..tools import sizing, quotes, timeline, drafts
from .. import rules, replan
from . import prompts
from .models import BillData, QuoteData

DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"
# Free-tier quotas are per model per day, so a quota error moves on to the next model in GEMINI_MODEL_ID.
DEFAULT_GEMINI_CHAIN = "gemini-3.5-flash,gemini-3.1-flash-lite,gemini-3.5-flash-lite,gemini-2.5-flash,gemini-2.5-flash-lite,gemini-flash-lite-latest,gemini-3-flash-preview"
# Backup providers, tried in this order after Gemini: name -> (base URL, env prefix, default model chain)
BACKUPS = {
    "bazaarlink": ("https://api.bazaarlink.ai/v1", "BAZAARLINK", "qwen/qwen3.7-flash:free,deepseek/deepseek-v4-flash-0731free:free"),
}
log = logging.getLogger(__name__)
_active_model: ContextVar[str | None] = ContextVar("active_model", default=None)
_exhausted: set[str] = set()              # models that hit their quota in this process (a warm Lambda keeps it)

def provider() -> str:
    return os.environ.get("MODEL_PROVIDER", "gemini")

def gemini_models() -> list[str]:
    return [m.strip() for m in os.environ.get("GEMINI_MODEL_ID", DEFAULT_GEMINI_CHAIN).split(",") if m.strip()]

def backups() -> list[str]:
    """Backup providers with a key set, in fallback order."""
    return [name for name, (_, env, _) in BACKUPS.items()
            if os.environ.get(f"{env}_API_KEY") or os.environ.get(f"{env}_KEY_PARAM")]

def backup_models() -> list[str]:
    """'provider:model' ids for the backup providers, e.g. 'bazaarlink:qwen/qwen3.7-flash:free'."""
    out = []
    for name in backups():
        _, env, default = BACKUPS[name]
        out += [f"{name}:{m.strip()}" for m in os.environ.get(f"{env}_MODEL_ID", default).split(",") if m.strip()]
    return out

def _backup_of(mid: str) -> str | None:
    name = mid.split(":", 1)[0]
    return name if ":" in mid and name in BACKUPS else None

def _retry_seconds(text: str) -> float | None:
    m = re.search(r"retry in ([0-9.]+)s", text)                      # Google
    if m:
        return float(m.group(1))
    m = re.search(r"try again in (?:([0-9]+)m)?([0-9.]+)s", text)    # OpenAI-style: "try again in 1m3.5s"
    return int(m.group(1) or 0) * 60 + float(m.group(2)) if m else None

def _failure_kind(e: BaseException) -> tuple[str | None, float]:
    """Classify a model error: ('daily', 0) quota used up for today (skip this model from now on), ('minute', seconds)
    per-minute limit (wait, retry once, then move on), ('busy', 0) temporary overload (try the next model), or
    (None, 0) a real error that should be raised."""
    names, parts, seen = [], [], set()
    while e is not None and id(e) not in seen:          # the details sit in the underlying Google error
        seen.add(id(e))
        names.append(type(e).__name__)
        parts.append(str(e))
        e = e.__cause__ or e.__context__
    text = " ".join(parts)
    if "ModelThrottledException" in names or any(s in text for s in ("RESOURCE_EXHAUSTED", "429")):
        wait = _retry_seconds(text)
        if "PerDay" in text or "per day" in text or (wait or 0) > 60:   # Google "PerDay"; OpenAI-style "per day"
            return "daily", 0
        return "minute", min(wait, 60) if wait is not None else 10
    if any(s in text for s in ("503", "UNAVAILABLE", "overloaded", "high demand")):
        return "busy", 0
    if "APIError" in names or any(s in text for s in ("Tool call validation failed", "tool_use_failed", "failed_generation")):
        return "busy", 0        # a streamed provider error, usually a garbled tool call; try the next model
    return None, 0

def _is_quota(e: BaseException) -> bool:
    return _failure_kind(e)[0] in ("daily", "minute")

_pool = ThreadPoolExecutor(max_workers=4)

class AITimeout(TimeoutError):
    """The AI did not answer within the time budget (the caller falls back to plain code)."""

def run_with_fallback(fn, budget: float | None = None, documents: bool = False):
    """Run fn() (which builds agents and calls them) on the first model with quota left; on a quota or overload error,
    retry on the next model. With a budget (seconds), give up with AITimeout when time runs out, so a request that
    API Gateway will cut off at 30 s can fall back to the plain-code path in time. documents=True (PDF/photo reading)
    leaves out the backup providers, which are only used for text."""
    deadline = time.monotonic() + budget if budget else None

    def remaining():
        return None if deadline is None else deadline - time.monotonic()

    def attempt():
        left = remaining()
        if left is None:
            return fn()
        if left <= 1:
            raise AITimeout("the AI did not answer in time")
        future = _pool.submit(contextvars.copy_context().run, fn)
        try:
            return future.result(timeout=left)
        except FutureTimeout:
            raise AITimeout("the AI did not answer in time")

    if provider() != "gemini":
        return attempt()
    last = None
    for mid in gemini_models() + ([] if documents else backup_models()):
        if mid in _exhausted:
            continue
        token = _active_model.set(mid)
        try:
            for n in (1, 2):
                try:
                    return attempt()
                except AITimeout:
                    raise
                except Exception as e:
                    kind, wait = _failure_kind(e)
                    if kind is None:
                        raise
                    last = e
                    log.warning("model %s: %s limit or fault (%s); %s", mid, kind, type(e).__name__,
                                "retrying" if kind == "minute" and n == 1 else "moving to the next model")
                    if kind == "daily":
                        _exhausted.add(mid)
                    left = remaining()
                    wait = min(wait, 5 if (budget and budget <= 30) else 30)   # short inside a request, longer in the background
                    if kind == "minute" and n == 1 and (left is None or left > wait + 3):
                        time.sleep(wait)                  # the provider says when the minute window frees up
                        continue
                    break
        finally:
            _active_model.reset(token)
    raise RuntimeError("every configured AI model is busy or has reached its daily free quota; try again later") from last

@lru_cache(maxsize=1)
def _ssm_secret(name: str) -> str:
    import boto3
    return boto3.client("ssm").get_parameter(Name=name, WithDecryption=True)["Parameter"]["Value"]

def gemini_key() -> str | None:
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    return _ssm_secret(os.environ["GEMINI_KEY_PARAM"]) if os.environ.get("GEMINI_KEY_PARAM") else None

def backup_key(name: str) -> str | None:
    env = BACKUPS[name][1]
    if os.environ.get(f"{env}_API_KEY"):
        return os.environ[f"{env}_API_KEY"]
    return _ssm_secret(os.environ[f"{env}_KEY_PARAM"]) if os.environ.get(f"{env}_KEY_PARAM") else None

def active_model() -> str | None:
    return _active_model.get()

def configured() -> bool:
    """Is a model available for the live agents?"""
    if provider() == "gemini":
        return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_KEY_PARAM"))
    return bool(os.environ.get("BEDROCK_MODEL_ID"))

def model():
    if provider() == "gemini":
        from strands.models.gemini import GeminiModel
        key = gemini_key()
        if not key:
            raise RuntimeError("Set GEMINI_API_KEY (local) or GEMINI_KEY_PARAM (SSM parameter on AWS).")
        mid = _active_model.get() or next((m for m in gemini_models() if m not in _exhausted), gemini_models()[0])
        backup = _backup_of(mid)
        if backup:
            from strands.models.openai import OpenAIModel
            return OpenAIModel(client_args={"api_key": backup_key(backup), "base_url": BACKUPS[backup][0], "max_retries": 0},
                               model_id=mid.split(":", 1)[1], params={"temperature": 0.1, "max_tokens": 4096})
        return GeminiModel(client_args={"api_key": key}, model_id=mid, params={"temperature": 0.1})
    from strands.models import BedrockModel
    model_id = os.environ.get("BEDROCK_MODEL_ID")
    if not model_id:
        raise RuntimeError("Set BEDROCK_MODEL_ID to a model (or inference profile) enabled for your account.")
    return BedrockModel(model_id=model_id, region_name=os.environ.get("AWS_REGION", "ap-south-1"), temperature=0.1)

# ---- thin @tool wrappers: the logic lives in solarsabha.tools, tested without any LLM ----
@tool
def get_rule(key: str) -> dict:
    """Get one rule from the rulebook with its value, source, status and date."""
    return rules.get_rule(key)

@tool
def size_system(annual_kwh: float, flats: int) -> dict:
    """Recommend a solar size in kW for common-area use, within the subsidy ceiling."""
    return sizing.size_system(annual_kwh, flats)

@tool
def money_summary(kw: float) -> dict:
    """Cost, subsidy, net cost, yearly saving, payback and CO2 for a system size."""
    return sizing.money_summary(kw)

@tool
def audit_quote(quote: dict) -> dict:
    """Run the deterministic risk checks on one extracted quote. Returns flags and a GREEN/AMBER/RED verdict."""
    return quotes.audit_quote(quote)

@tool
def check_vendor(name: str) -> dict:
    """Check a vendor against the loaded (sample) approved list."""
    return quotes.check_vendor(name)

@tool
def build_timeline(events: list, today_day: int) -> list:
    """Per-stage status of the project: DONE, ACTIVE, OVERDUE, WAITING."""
    return timeline.build_timeline(events, today_day)

@tool
def next_action(timeline_rows: list) -> dict:
    """What needs attention now and how hard to chase (0 none, 1 reminder, 2 escalation)."""
    return timeline.next_action(timeline_rows)

@tool
def classify_reply(text: str) -> dict:
    """Classify a DISCOM reply (LOAD_LIMIT, APPROVED, DOCUMENTS_NEEDED, UNCLEAR)."""
    return replan.classify_reply(text)

@tool
def replan_for_load_limit(annual_kwh: float, flats: int, max_kw: float) -> dict:
    """Recompute the solar size when the DISCOM limits the permitted capacity."""
    return replan.replan_for_load_limit(annual_kwh, flats, max_kw)

@tool
def draft_discom_reminder(stage_label: str, overdue_days: int, application_ref: str) -> dict:
    """Draft (not send) a polite reminder to the DISCOM."""
    return drafts.discom_reminder(stage_label, overdue_days, application_ref)

@tool
def draft_discom_escalation(stage_label: str, overdue_days: int, application_ref: str) -> dict:
    """Draft (not send) an escalation to the grievance cell."""
    return drafts.discom_escalation(stage_label, overdue_days, application_ref)

MCP_FOR = {"secretary": {"get_rule", "list_rules", "size_system", "money_summary"},
           "auditor": {"get_rule", "list_rules", "check_vendor", "scan_for_injection"}}

def _with_mcp(builtin: list, extra: list | None, role: str) -> list:
    """SolarRules MCP tools replace built-ins with the same name (one trusted source of rules and maths);
    each agent takes only the MCP tools that fit its job."""
    mcp = {t.tool_name: t for t in (extra or []) if t.tool_name in MCP_FOR[role]}
    return [t for t in builtin if t.tool_name not in mcp] + list(mcp.values())

def _agent_kwargs() -> dict:
    """Gemini free-tier limits are daily, so long back-offs only waste time: retry once quickly, then let
    run_with_fallback move to the next model. The backup providers limit tokens per minute and ask for waits of
    seconds, so they get a few more, slower retries. Bedrock keeps Strands' default retries."""
    if provider() != "gemini":
        return {}
    from strands import ModelRetryStrategy
    if _backup_of(_active_model.get() or ""):
        return {"retry_strategy": ModelRetryStrategy(max_attempts=4, initial_delay=4, max_delay=15)}
    return {"retry_strategy": ModelRetryStrategy(max_attempts=2, initial_delay=2, max_delay=4)}

def _hooks(trace, name, tools, extra=()):
    allowed = {t.tool_name for t in tools} | set(extra)
    return [TraceHooks(trace, name, allowed)]

def build_reader(trace: Trace | None = None) -> Agent:
    return Agent(name="reader", description="Reads bills and quotes (photos or PDFs) into structured fields.",
                 model=model(), system_prompt=prompts.READER, tools=[], hooks=_hooks(trace, "Reader", []),
                 callback_handler=null_callback_handler, **_agent_kwargs())

def build_auditor(trace: Trace | None = None, extra_tools: list | None = None) -> Agent:
    tools = _with_mcp([audit_quote, check_vendor, get_rule], extra_tools, "auditor")
    return Agent(name="auditor", description="Audits vendor quotes for risks and explains the flags in plain words.",
                 model=model(), system_prompt=prompts.AUDITOR, tools=tools, hooks=_hooks(trace, "Auditor", tools),
                 callback_handler=null_callback_handler, **_agent_kwargs())

def build_chaser(trace: Trace | None = None) -> Agent:
    tools = [build_timeline, next_action, classify_reply, replan_for_load_limit, draft_discom_reminder, draft_discom_escalation, get_rule]
    return Agent(name="chaser", description="Tracks the timeline, reads DISCOM replies, drafts follow-ups and re-plans.",
                 model=model(), system_prompt=prompts.CHASER, tools=tools, hooks=_hooks(trace, "Chaser", tools),
                 callback_handler=null_callback_handler, **_agent_kwargs())

def _specialist(name: str, description: str, build):
    """Expose a specialist agent to the Secretary as a tool ('agents as tools'). Each call builds a fresh agent on the
    model the Secretary is using: a shared agent instance refuses a second call while it is busy, and stays busy after
    a failed one. If the model runs out of quota inside the specialist, the Secretary is stopped and ask() re-raises
    the error, so run_with_fallback moves the whole review to the next model instead of the Secretary retrying."""
    mid = _active_model.get()

    @tool(name=name, description=description, context=True)
    def call(input: str, tool_context: ToolContext) -> str:
        """Ask the specialist. input: the question or task, with the facts it needs."""
        token = _active_model.set(mid)
        try:
            return str(build()(input)).strip()
        except Exception as e:
            if _failure_kind(e)[0] is None:
                raise
            tool_context.agent.specialist_failure = e
            tool_context.agent.cancel()
            return f"{name} could not run: the model is out of quota"
        finally:
            _active_model.reset(token)
    return call

def ask(agent: Agent, prompt: str, **kwargs):
    """Call an agent; if one of its specialists hit a quota or overload error, raise that error."""
    try:
        result = agent(prompt, **kwargs)
    except Exception as e:
        failure = getattr(agent, "specialist_failure", None)
        if failure is not None:
            raise failure from e
        raise
    failure = getattr(agent, "specialist_failure", None)
    if failure is not None:
        raise failure
    return result

def build_writer(trace: Trace | None = None) -> Agent:
    """The Secretary without tools, for rewording a letter: nothing to look up, and a model given tools it must not use
    sometimes calls one anyway."""
    return Agent(name="secretary", description="Rewords the committee's letters.", model=model(),
                 system_prompt=prompts.SECRETARY, tools=[], hooks=_hooks(trace, "Secretary", []),
                 callback_handler=null_callback_handler, **_agent_kwargs())

def build_secretary(trace: Trace | None = None, extra_tools: list | None = None) -> Agent:
    """Coordinator using the 'agents as tools' pattern: specialists are exposed to it as tools."""
    tools = [_specialist("reader", "Reads bills and quotes into structured fields.", lambda: build_reader(trace)),
             _specialist("auditor", "Audits vendor quotes for risks and explains the flags in plain words.",
                         lambda: build_auditor(trace, extra_tools)),
             _specialist("chaser", "Tracks the timeline, reads DISCOM replies, drafts follow-ups and re-plans.",
                         lambda: build_chaser(trace))] +         _with_mcp([size_system, money_summary, get_rule], extra_tools, "secretary")
    return Agent(name="secretary", description="Coordinator that talks to the committee.", model=model(),
                 system_prompt=prompts.SECRETARY, tools=tools, hooks=_hooks(trace, "Secretary", tools),
                 tool_executor=SequentialToolExecutor(),         # one specialist at a time keeps the trace in order
                 callback_handler=null_callback_handler, **_agent_kwargs())
