"""Build the model and the agents. Needs AWS credentials and Bedrock model access (see docs/SETUP_AWS.md).
NOTE: written against strands-agents 1.58. Not exercised against a live Bedrock model in this repo's CI.
Run `python scripts/smoke_live.py` once credentials are ready; fix anything it reports first."""
import os
from strands import Agent, tool
from strands.models import BedrockModel
from strands.handlers.callback_handler import null_callback_handler
from ..trace import Trace, TraceHooks
from ..tools import sizing, quotes, timeline, drafts
from .. import rules, replan
from . import prompts
from .models import BillData, QuoteData

def model() -> BedrockModel:
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

def _hooks(trace, name, tools, extra=()):
    allowed = {t.tool_name for t in tools} | set(extra)
    return [TraceHooks(trace, name, allowed)]

def build_reader(trace: Trace | None = None) -> Agent:
    return Agent(name="reader", description="Reads bills and quotes (photos or PDFs) into structured fields.",
                 model=model(), system_prompt=prompts.READER, tools=[], hooks=_hooks(trace, "Reader", []),
                 callback_handler=null_callback_handler)

def build_auditor(trace: Trace | None = None, extra_tools: list | None = None) -> Agent:
    tools = _with_mcp([audit_quote, check_vendor, get_rule], extra_tools, "auditor")
    return Agent(name="auditor", description="Audits vendor quotes for risks and explains the flags in plain words.",
                 model=model(), system_prompt=prompts.AUDITOR, tools=tools, hooks=_hooks(trace, "Auditor", tools),
                 callback_handler=null_callback_handler)

def build_chaser(trace: Trace | None = None) -> Agent:
    tools = [build_timeline, next_action, classify_reply, replan_for_load_limit, draft_discom_reminder, draft_discom_escalation, get_rule]
    return Agent(name="chaser", description="Tracks the timeline, reads DISCOM replies, drafts follow-ups and re-plans.",
                 model=model(), system_prompt=prompts.CHASER, tools=tools, hooks=_hooks(trace, "Chaser", tools),
                 callback_handler=null_callback_handler)

def build_secretary(trace: Trace | None = None, extra_tools: list | None = None) -> Agent:
    """Coordinator using the 'agents as tools' pattern: specialists are exposed to it as tools."""
    reader, auditor, chaser = build_reader(trace), build_auditor(trace, extra_tools), build_chaser(trace)
    tools = [reader.as_tool(name="reader"), auditor.as_tool(name="auditor"), chaser.as_tool(name="chaser")] +         _with_mcp([size_system, money_summary, get_rule], extra_tools, "secretary")
    return Agent(name="secretary", description="Coordinator that talks to the committee.", model=model(),
                 system_prompt=prompts.SECRETARY, tools=tools, hooks=_hooks(trace, "Secretary", tools),
                 callback_handler=null_callback_handler)
