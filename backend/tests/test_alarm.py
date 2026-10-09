"""The Chaser's alarm clock: when it rings, and that it is created, moved and removed correctly."""
import json
from datetime import date, datetime, timezone

from solarsabha import alarm
from solarsabha import project as P
from solarsabha.schemas import CreateProject

def sample(offset=0):
    doc, _ = P.create("abcdef0123", CreateProject(sample=True))
    doc["sim_offset_days"] = offset
    return P.recompute(doc)

def test_wakes_on_the_day_the_active_stage_is_due():
    doc = sample()
    started = date.fromisoformat(doc["started_on"])
    feas = next(s for s in doc["result"]["timeline"] if s["key"] == "FEASIBILITY")
    when = alarm.next_wake(doc, today=started)
    assert when.date() == date.fromordinal(started.toordinal() + feas["start_day"] + feas["max_days"])
    assert when.tzinfo == timezone.utc

def test_late_stage_wakes_again_in_a_week():
    doc = sample(offset=40)                                    # simulated: feasibility is overdue
    late_today = date.fromordinal(date.fromisoformat(doc["started_on"]).toordinal() + 60)
    assert alarm.next_wake(doc, today=late_today).date() == date.fromordinal(late_today.toordinal() + 7)

def test_nothing_pending_means_no_alarm():
    doc = sample()
    for s in doc["result"]["timeline"]:
        s["status"] = "DONE"
    assert alarm.next_wake(doc) is None

class FakeScheduler:
    class exceptions:
        class ResourceNotFoundException(Exception):
            pass
    def __init__(self):
        self.schedules, self.calls = {}, []
    def update_schedule(self, **spec):
        if spec["Name"] not in self.schedules:
            raise self.exceptions.ResourceNotFoundException()
        self.calls.append("update"); self.schedules[spec["Name"]] = spec
    def create_schedule(self, **spec):
        self.calls.append("create"); self.schedules[spec["Name"]] = spec
    def delete_schedule(self, Name):
        self.calls.append("delete"); self.schedules.pop(Name, None)

def test_sync_creates_then_moves_then_removes(monkeypatch):
    fake = FakeScheduler()
    monkeypatch.setenv("SCHEDULER_ROLE_ARN", "arn:aws:iam::123:role/sched")
    monkeypatch.setenv("WAKE_FUNCTION_ARN", "arn:aws:lambda:ap-south-1:123:function:wake")
    monkeypatch.setattr(alarm, "_client", lambda: fake)
    doc = sample()
    assert alarm.sync(doc) and fake.calls == ["create"]
    spec = fake.schedules["solarsabha-abcdef0123"]
    assert spec["ScheduleExpression"].startswith("at(") and spec["ActionAfterCompletion"] == "DELETE"
    assert json.loads(spec["Target"]["Input"]) == {"project_id": "abcdef0123"}
    alarm.sync(doc)
    assert fake.calls == ["create", "update"]
    for s in doc["result"]["timeline"]:
        s["status"] = "DONE"
    assert alarm.sync(doc) is None and fake.calls[-1] == "delete" and not fake.schedules

def test_disabled_outside_aws(monkeypatch):
    monkeypatch.delenv("SCHEDULER_ROLE_ARN", raising=False)
    assert alarm.sync(sample()) is None
