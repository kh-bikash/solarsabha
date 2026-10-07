"""Scheduled wake-up (EventBridge Scheduler -> Lambda). In production the clock is real; in the demo the
'advance' endpoint simulates the same wake-up. Both call the same Chaser logic."""
from ..state import get_store
from .api import _recompute

def handler(event, context=None):
    pid = event["project_id"]
    store = get_store(); doc = store.get(pid)
    if not doc:
        return {"ok": False}
    doc["today_day"] = event.get("today_day", doc["today_day"] + 1)
    doc = _recompute(doc); store.put(pid, doc)
    return {"ok": True, "next_action": doc["result"]["next_action"]}
