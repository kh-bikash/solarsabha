"""When the DISCOM replies, update the plan. Rule-based fallback; the Chaser agent does the same job with an LLM
in live mode and must produce the same structured result."""
import re
from .tools import sizing

LOAD_PATTERN = re.compile(r"sanctioned\s+load.{0,200}?(\d+(?:\.\d+)?)\s*kw", re.I | re.S)

def classify_reply(text: str) -> dict:
    t = text.lower()
    m = LOAD_PATTERN.search(text)
    if m and any(w in t for w in ["insufficient", "inadequate", "too low", "exceed", "not sufficient", "limit"]):
        return {"type": "LOAD_LIMIT", "max_kw": float(m.group(1))}
    if any(w in t for w in ["approved", "feasibility granted", "feasible"]):
        return {"type": "APPROVED"}
    if any(w in t for w in ["additional document", "please submit", "resubmit"]):
        return {"type": "DOCUMENTS_NEEDED"}
    return {"type": "UNCLEAR"}

def replan_for_load_limit(annual_kwh: float, flats: int, max_kw: float) -> dict:
    plan = sizing.size_system(annual_kwh, flats, max_kw_override=max_kw)
    return plan
