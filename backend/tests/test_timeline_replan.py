from solarsabha.tools import timeline
from solarsabha import replan

EVENTS = [{"stage": "AGM", "done_day": 7}, {"stage": "PORTAL", "done_day": 9}]

def test_active_then_overdue_then_escalation():
    assert timeline.next_action(timeline.build_timeline(EVENTS, 20))["status"] == "ACTIVE"
    n = timeline.next_action(timeline.build_timeline(EVENTS, 40))     # 31 days in a 25-day stage
    assert n["status"] == "OVERDUE" and n["chase_level"] == 1
    n = timeline.next_action(timeline.build_timeline(EVENTS, 50))     # 41 days in stage
    assert n["chase_level"] == 2

def test_classify_load_limit_reply():
    r = replan.classify_reply("The sanctioned load for the common meter is insufficient. Maximum permissible solar is 25 kW.")
    assert r == {"type": "LOAD_LIMIT", "max_kw": 25.0}

def test_replan_respects_limit():
    assert replan.replan_for_load_limit(60000, 50, 25)["recommended_kw"] == 25
