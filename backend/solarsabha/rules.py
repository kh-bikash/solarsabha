"""Rulebook access. Every number the agents use must come from here so it can be cited."""
import json
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).parent / "data"

@lru_cache(maxsize=1)
def _book() -> dict:
    return json.loads((DATA / "rulebook.json").read_text())["rules"]

def get_rule(key: str) -> dict:
    """Return one rule with its value, source, status and date. Raises KeyError if unknown."""
    book = _book()
    if key not in book:
        raise KeyError(f"Unknown rule '{key}'. Known: {sorted(book)}")
    return {"key": key, **book[key]}

def value(key: str):
    return get_rule(key)["value"]

def list_rules() -> list:
    return [{"key": k, **v} for k, v in _book().items()]

def approved_vendors() -> list:
    return json.loads((DATA / "approved_vendors_sample.json").read_text())["vendors"]
