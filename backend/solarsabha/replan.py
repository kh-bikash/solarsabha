"""When the DISCOM replies, update the plan. Rule-based fallback; the Chaser agent does the same job with an LLM
in live mode and must produce the same structured result."""
import re
from .tools import sizing

LOAD_PATTERN = re.compile(r"sanctioned\s+load.{0,200}?(\d+(?:\.\d+)?)\s*kw", re.I | re.S)
# "can permit only upto 30 kW", "maximum permissible ... 25 kW", "restricted to 20 kW"
CAP_PATTERN = re.compile(r"(?:permit\w*|permissible|allow\w*|restrict\w*|limit\w*|only|max\w*|up\s*to|upto)"
                         r"[^.\d]{0,40}?(\d+(?:\.\d+)?)\s*kw", re.I)
CONSTRAINT_WORDS = ["insufficient", "inadequate", "too low", "exceed", "not sufficient", "limit", "constrain",
                    "restrict", "permit only", "only up", "only upto", "maximum permissible"]

def classify_reply(text: str) -> dict:
    t = text.lower()
    m = LOAD_PATTERN.search(text) or CAP_PATTERN.search(text)
    if m and any(w in t for w in CONSTRAINT_WORDS):
        return {"type": "LOAD_LIMIT", "max_kw": float(m.group(1))}
    if any(w in t for w in ["approved", "feasibility granted", "feasible"]):
        return {"type": "APPROVED"}
    if any(w in t for w in ["additional document", "please submit", "resubmit"]):
        return {"type": "DOCUMENTS_NEEDED"}
    return {"type": "UNCLEAR"}

def replan_for_load_limit(annual_kwh: float, flats: int, max_kw: float) -> dict:
    plan = sizing.size_system(annual_kwh, flats, max_kw_override=max_kw)
    return plan
