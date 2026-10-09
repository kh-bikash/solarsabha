"""Scheduled wake-up (EventBridge Scheduler -> Lambda), event: {"project_id": "<id>"}.

The agent does not wait for weeks: it saves its notes and sets an alarm. When the alarm rings, this re-reads the
project, recomputes it against today's date (the Chaser's logic), saves it, and reports what needs attention.
In the demo the time machine moves a simulated clock through the same recompute."""
import json
import logging

from .. import project as P
from ..state import get_store

log = logging.getLogger("solarsabha.wake")

def handler(event, context=None):
    pid = event.get("project_id")
    store = get_store()
    doc = store.get(pid) if pid else None
    if not doc:
        return {"ok": False, "reason": "unknown or expired project"}
    before = doc.get("result", {}).get("next_action", {})
    doc = P.recompute(doc)
    after = doc["result"]["next_action"]
    if after != before:
        P.log(doc, "Chaser (scheduled)", "woke up and re-checked the timeline",
              f"{after['label']}: {after['status'].lower()}" + (f", {after['overdue_by']} days late" if after.get("overdue_by") else ""))
    store.put(pid, doc)
    log.info(json.dumps({"event": "wake", "project": pid, "next_action": after}))
    return {"ok": True, "next_action": after}
