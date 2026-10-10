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


def test_informal_capacity_limit_is_a_load_limit():
    messy = ("Sir, w.r.t. ur appln for rooftop solar, transformer capacity at ur sub-station is constrained, we can "
             "permit only upto 30 kW. Kindly revise and resubmit. - JE, NVVNL")
    assert replan.classify_reply(messy) == {"type": "LOAD_LIMIT", "max_kw": 30.0}
    assert replan.classify_reply("Feasibility approved for the full 36 kW.")["type"] == "APPROVED"
    assert replan.classify_reply("Feasibility approved for capacity up to 36 kW.")["type"] == "APPROVED"
