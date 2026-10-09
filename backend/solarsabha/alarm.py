"""The Chaser's alarm clock: one EventBridge Scheduler one-time schedule per project.

An agent does not wait for weeks. After every change, the project's alarm is set for the day the active stage is due
(or a week from now if it is already late, so the Chaser keeps following up). When it rings, WakeFunction recomputes the
project and sets the next alarm. Active only on AWS (SCHEDULER_ROLE_ARN and WAKE_FUNCTION_ARN are set by template.yaml);
a scheduler problem is logged and never breaks a save."""
import json
import logging
import os
from datetime import date, datetime, time, timedelta, timezone

log = logging.getLogger("solarsabha.alarm")
FOLLOW_UP_DAYS = 7
WAKE_HOUR_UTC = 3                      # 08:30 in India

def next_wake(doc: dict, today: date | None = None) -> datetime | None:
    """When the Chaser should next look at this project, on the real calendar. None if nothing is pending."""
    r = doc.get("result") or {}
    active = next((s for s in r.get("timeline", []) if s["status"] in ("ACTIVE", "OVERDUE")), None)
    if not active:
        return None
    today = today or datetime.now(timezone.utc).date()
    started = date.fromisoformat(doc["started_on"])
    due = started + timedelta(days=active["start_day"] + active["max_days"])     # simulated days are not real days
    when = due if due > today else today + timedelta(days=FOLLOW_UP_DAYS)
    return datetime.combine(when, time(WAKE_HOUR_UTC), tzinfo=timezone.utc)

def _enabled() -> bool:
    return bool(os.environ.get("SCHEDULER_ROLE_ARN") and os.environ.get("WAKE_FUNCTION_ARN"))

def _client():
    import boto3
    return boto3.client("scheduler")

def name(pid: str) -> str:
    return f"solarsabha-{pid}"

def sync(doc: dict) -> str | None:
    """Create, move or remove the project's alarm. Returns the ISO time set, or None."""
    if not _enabled():
        return None
    when = next_wake(doc)
    try:
        client = _client()
        if when is None:
            remove(doc["id"], client)
            return None
        spec = {"Name": name(doc["id"]), "ScheduleExpression": f"at({when.strftime('%Y-%m-%dT%H:%M:%S')})",
                "ScheduleExpressionTimezone": "UTC", "FlexibleTimeWindow": {"Mode": "OFF"},
                "ActionAfterCompletion": "DELETE",
                "Target": {"Arn": os.environ["WAKE_FUNCTION_ARN"], "RoleArn": os.environ["SCHEDULER_ROLE_ARN"],
                           "Input": json.dumps({"project_id": doc["id"]})}}
        try:
            client.update_schedule(**spec)
        except client.exceptions.ResourceNotFoundException:
            client.create_schedule(**spec)
        return when.isoformat()
    except Exception:
        log.exception(json.dumps({"event": "alarm_failed", "project": doc.get("id")}))
        return None

def remove(pid: str, client=None):
    if not _enabled():
        return
    try:
        (client or _client()).delete_schedule(Name=name(pid))
    except Exception as e:                      # already gone is fine
        if "ResourceNotFound" not in type(e).__name__:
            log.exception(json.dumps({"event": "alarm_delete_failed", "project": pid}))
