"""Stage tracking and chasing logic. Deterministic. The Chaser agent only polishes the wording of drafts."""
from .. import rules

def build_timeline(events, today_day) -> list:
    """events: [{'stage': 'AGM', 'done_day': 7}, ...]. Day numbers count from project start (day 0).
    Returns per-stage status: DONE, ACTIVE, OVERDUE, WAITING."""
    stages = rules.value("stages")
    done = {e["stage"]: e["done_day"] for e in events}
    out, start, active_found = [], 0, False
    for s in stages:
        if s["key"] in done:
            out.append({**s, "status": "DONE", "start_day": start, "done_day": done[s["key"]]})
            start = done[s["key"]]
        elif not active_found:
            active_found = True
            elapsed = today_day - start
            out.append({**s, "status": "OVERDUE" if elapsed > s["max_days"] else "ACTIVE", "start_day": start,
                        "days_elapsed": elapsed, "overdue_by": max(0, elapsed - s["max_days"])})
        else:
            out.append({**s, "status": "WAITING"})
    return out

def chase_level(stage) -> int:
    """0 = fine, 1 = polite reminder, 2 = escalation to grievance cell."""
    if stage.get("status") != "OVERDUE":
        return 0
    return 2 if stage["overdue_by"] > 7 else 1

def next_action(timeline) -> dict:
    for s in timeline:
        if s["status"] in ("ACTIVE", "OVERDUE"):
            return {"stage": s["key"], "label": s["label"], "chase_level": chase_level(s), "status": s["status"],
                    "overdue_by": s.get("overdue_by", 0)}
    return {"stage": None, "label": "Complete", "chase_level": 0, "status": "DONE", "overdue_by": 0}
