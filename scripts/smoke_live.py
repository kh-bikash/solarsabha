"""First thing to run once AWS credentials and Bedrock model access are ready. Reports what is broken.
Usage: BEDROCK_MODEL_ID=<id> AWS_REGION=ap-south-1 python scripts/smoke_live.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from solarsabha.agents import factory
from solarsabha.agents.mcp_tools import solar_rules_mcp
from solarsabha.trace import Trace

t = Trace()
print("1) model + plain agent")
a = factory.build_auditor(t)
print(str(a("Call audit_quote for vendor 'Sasta Sun Traders', capacity_kw 36, total_price_inr 1400000, advance_pct 20. Summarise in two sentences."))[:400])
print("2) MCP tools")
with solar_rules_mcp() as tools:
    print([x.tool_name for x in tools])
    s = factory.build_secretary(t, extra_tools=tools)
    print(str(s("Society has 50 flats and uses 60000 kWh a year. What size and what does it cost? Cite the subsidy rule source."))[:600])
print("trace events:", len(t.events))
