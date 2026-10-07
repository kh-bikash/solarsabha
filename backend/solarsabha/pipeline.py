"""The offline pipeline: the whole product loop with NO LLM and NO AWS. Teammates can run it anywhere, and the
frontend's demo data is generated from it. Live mode (agents/) replaces only the *reading* and *explaining*
steps; all numbers still come from these same tools."""
import json
from pathlib import Path
from . import rules, replan
from .trace import Trace
from .tools import sizing, quotes, fairness, negotiation, drafts, timeline

SAMPLES = Path(__file__).resolve().parents[1] / "samples"

def load_sample_inputs(folder: Path = SAMPLES) -> dict:
    return json.loads((folder / "society.json").read_text())

def run_offline(inputs: dict | None = None, today_day: int = 0, events: list | None = None,
                discom_reply: str | None = None) -> dict:
    inputs = inputs or load_sample_inputs()
    tr = Trace()
    soc = inputs["society"]
    tr.note("Secretary", f"New project for {soc['name']} ({soc['flats']} flats). Starting with the bills.")

    # 1. Reader: bills -> annual kWh (offline: values come from the sample's extracted JSON)
    bills = inputs["bills"]
    annual = tr.call("Reader", "sum_bills", lambda bills: sum(b["units_kwh"] for b in bills), bills=bills)
    unclear = [b["month"] for b in bills if b.get("unclear")]
    if unclear:
        tr.note("Reader", f"Unclear values in: {', '.join(unclear)}. Asking the committee to confirm.")

    # 2. Sizing tools (plain code, called by the Secretary; the Planner is not an agent)
    plan = tr.call("Secretary", "size_system", sizing.size_system, annual_kwh=annual, flats=soc["flats"])
    rec_kw = plan["recommended_kw"]
    money = {o["label"]: tr.call("Secretary", "money_summary", sizing.money_summary, kw=o["kw"]) for o in plan["options"]}
    rec = money["recommended"]

    # 3. Auditor: quotes
    audits, negs = [], []
    for q in inputs["quotes"]:
        a = tr.call("Auditor", "audit_quote", quotes.audit_quote, q=q)
        audits.append(a)
        tr.note("Auditor", f"{q['vendor']}: {a['verdict']} ({len(a['flags'])} flag(s))")
    # 4. Simulated negotiation (plain code)
    for q, a in zip(inputs["quotes"], audits):
        negs.append(tr.call("Secretary", "run_simulated_negotiation", negotiation.run_simulated_negotiation, quote=q, audit=a))

    # 5. Fairness
    fair = tr.call("Secretary", "fairness_table", fairness.fairness_table,
                   net_cost=rec["net_cost"], saving_per_year=rec["saving_per_year"], flat_areas_sqft=inputs["flat_areas_sqft"], total_flats=soc["flats"])

    # 6. Timeline + Chaser
    ev = events if events is not None else inputs.get("events", [])
    tl = tr.call("Chaser", "build_timeline", timeline.build_timeline, events=ev, today_day=today_day)
    nxt = timeline.next_action(tl)
    out_drafts = [drafts.agm_notice(soc["name"], rec_kw, rec["net_cost"], rec["subsidy"], rec["payback_years"], inputs.get("agm_date", "[date]")),
                  drafts.agm_resolution(soc["name"], rec_kw, "equal")]
    for q, a, n in zip(inputs["quotes"], audits, negs):
        if a["verdict"] == "RED":
            out_drafts.append(drafts.proof_request(q["vendor"]))
        elif not n.get("skipped"):
            out_drafts.append(drafts.counter_offer(q["vendor"], n["rounds"][0]["price"], n["rounds"][0]["advance_pct"], 5))
    tr.note("Secretary", f"Drafted {len(out_drafts)} papers for the committee: AGM notice, resolution and vendor letters. Nothing is sent.")
    if nxt["chase_level"] == 1:
        out_drafts.append(drafts.discom_reminder(nxt["label"], nxt["overdue_by"], soc.get("application_ref", "[ref]")))
        tr.note("Chaser", f"{nxt['label']} is {nxt['overdue_by']} days late. Drafted a polite reminder. Waiting for a human to approve.")
    elif nxt["chase_level"] == 2:
        out_drafts.append(drafts.discom_escalation(nxt["label"], nxt["overdue_by"], soc.get("application_ref", "[ref]")))
        tr.note("Chaser", f"{nxt['label']} is {nxt['overdue_by']} days overdue. Drafted an escalation. Waiting for a human to approve.")

    # 7. Optional DISCOM reply -> replan (Plan v1 vs v2)
    plan_v2 = None
    if discom_reply:
        cls = tr.call("Chaser", "classify_reply", replan.classify_reply, text=discom_reply)
        if cls["type"] == "LOAD_LIMIT":
            p2 = tr.call("Secretary", "replan_for_load_limit", replan.replan_for_load_limit,
                         annual_kwh=annual, flats=soc["flats"], max_kw=cls["max_kw"])
            m2 = sizing.money_summary(p2["recommended_kw"])
            plan_v2 = {"reason": f"DISCOM sanctioned-load limit of {cls['max_kw']:.0f} kW", "plan": p2, "money": m2}

    return {
        "mode": "offline", "simulated_parts": ["vendor replies", "DISCOM replies", "clock"],
        "society": soc, "annual_kwh": annual, "bills": bills, "price_band": rules.get_rule("price_band_per_kw")["value"],
        "plan": plan, "money": money, "recommended": rec, "plan_v2": plan_v2,
        "audits": audits, "negotiations": negs, "fairness": fair, "timeline": tl, "next_action": nxt,
        "drafts": out_drafts, "trace": tr.events, "today_day": today_day,
        "rules_used": [r["key"] for r in rules.list_rules() if r["key"] != "stages"],
    }

if __name__ == "__main__":
    print(json.dumps(run_offline(), indent=2)[:3000])
