"""Build the model and the agents. Needs AWS credentials and Bedrock model access (see docs/SETUP_AWS.md).
NOTE: written against strands-agents 1.58. Not exercised against a live Bedrock model in this repo's CI.
Run `python scripts/smoke_live.py` once credentials are ready; fix anything it reports first."""
import os
from strands import Agent, tool
from strands.models import BedrockModel
from ..trace import Trace, TraceHandler
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

def build_reader(trace: Trace | None = None) -> Agent:
    return Agent(name="reader", description="Reads bills and quotes (photos or PDFs) into structured fields.",
                 model=model(), system_prompt=prompts.READER, tools=[],
                 callback_handler=TraceHandler(trace, "Reader") if trace else None)

def build_auditor(trace: Trace | None = None, extra_tools: list | None = None) -> Agent:
    return Agent(name="auditor", description="Audits vendor quotes for risks and explains the flags in plain words.",
                 model=model(), system_prompt=prompts.AUDITOR, tools=[audit_quote, check_vendor, get_rule] + (extra_tools or []),
                 callback_handler=TraceHandler(trace, "Auditor") if trace else None)

def build_chaser(trace: Trace | None = None) -> Agent:
    return Agent(name="chaser", description="Tracks the timeline, reads DISCOM replies, drafts follow-ups and re-plans.",
                 model=model(), system_prompt=prompts.CHASER,
                 tools=[build_timeline, next_action, classify_reply, replan_for_load_limit, draft_discom_reminder, draft_discom_escalation, get_rule],
                 callback_handler=TraceHandler(trace, "Chaser") if trace else None)

def build_secretary(trace: Trace | None = None, extra_tools: list | None = None) -> Agent:
    """Coordinator using the 'agents as tools' pattern: specialists are exposed to it as tools."""
    reader, auditor, chaser = build_reader(trace), build_auditor(trace, extra_tools), build_chaser(trace)
    return Agent(name="secretary", description="Coordinator that talks to the committee.", model=model(),
                 system_prompt=prompts.SECRETARY,
                 tools=[reader.as_tool(name="reader"), auditor.as_tool(name="auditor"), chaser.as_tool(name="chaser"),
                        size_system, money_summary, get_rule] + (extra_tools or []),
                 callback_handler=TraceHandler(trace, "Secretary") if trace else None)
