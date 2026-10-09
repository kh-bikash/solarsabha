"""Rulebook access. Every number the agents use must come from here so it can be cited.

National rules live in data/rulebook.json under "rules". A state can override any rule under
"state_overrides" -> "<State>" -> "<rule key>" with the same shape (value, source, status, as_of). Overrides are
only added once verified; until then the national rule applies and the UI says so."""
import json
from contextlib import contextmanager
from contextvars import ContextVar
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).parent / "data"
_state: ContextVar[str | None] = ContextVar("rules_state", default=None)

INDIA_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", "Haryana",
    "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
]

@lru_cache(maxsize=1)
def _raw() -> dict:
    return json.loads((DATA / "rulebook.json").read_text(encoding="utf-8"))

def _book() -> dict:
    return _raw()["rules"]

def _overrides(state: str | None) -> dict:
    return _raw().get("state_overrides", {}).get(state or "", {}) if state else {}

@contextmanager
def use_state(state: str | None):
    """Within this block, rule lookups apply the given state's overrides (if any)."""
    token = _state.set(state)
    try:
        yield
    finally:
        _state.reset(token)

def get_rule(key: str) -> dict:
    """Return one rule with its value, source, status, date and scope. Raises KeyError if unknown."""
    book = _book()
    if key not in book:
        raise KeyError(f"Unknown rule '{key}'. Known: {sorted(book)}")
    state = _state.get()
    o = _overrides(state).get(key)
    return {"key": key, **o, "scope": state} if o else {"key": key, **book[key], "scope": "national"}

def value(key: str):
    return get_rule(key)["value"]

def list_rules() -> list:
    return [get_rule(k) for k in _book()]

def state_coverage(state: str | None) -> dict:
    """What the UI tells the committee about rules for their state."""
    n = len(_overrides(state))
    return {"state": state or None, "overrides": n,
            "message": (f"{n} rule(s) specific to {state} are loaded." if n else
                        "National rules apply. No state-specific rules are loaded yet; confirm local procedures with your DISCOM.")}

def approved_vendors() -> list:
    return json.loads((DATA / "approved_vendors_sample.json").read_text(encoding="utf-8"))["vendors"]
