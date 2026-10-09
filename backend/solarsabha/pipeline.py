"""The offline pipeline: the whole product loop with NO LLM and NO AWS. Teammates can run it anywhere, and the
frontend's demo data is generated from it. Live mode (agents/) replaces only the *reading* and *explaining*
steps; all numbers still come from these same tools.

It runs on whatever the committee has given so far: no bills yet means no plan yet, no quotes means no audit."""
import json
from pathlib import Path
from . import rules, replan
from .trace import Trace
from .tools import sizing, quotes, fairness, negotiation, drafts, timeline

SAMPLES = Path(__file__).resolve().parents[1] / "samples"
ASSUMPTION_RULES = {"tariff": "default_tariff_inr_per_kwh", "cost_per_kw": "cost_per_kw",
                    "yield_kwh_per_kw": "yield_kwh_per_kw_year", "share": "target_share_of_load"}

def load_sample_inputs(folder: Path = SAMPLES) -> dict:
    return json.loads((folder / "society.json").read_text(encoding="utf-8"))

def resolve_assumptions(overrides: dict | None) -> dict:
    """Each assumption with its value and where it came from: the committee, or the rulebook (cited)."""
    out = {}
    for k, rule_key in ASSUMPTION_RULES.items():
        v = (overrides or {}).get(k)
        out[k] = {"value": v, "source": "committee", "rule": rule_key} if v is not None else \
                 {"value": rules.value(rule_key), "source": "rulebook", "rule": rule_key}
    return out

def bill_average_rate(bills) -> float | None:
    """Average rupees per unit across bills that show both. Includes fixed charges and taxes, so it is only a
    hint for the committee, never applied automatically."""
    pairs = [(b["amount_inr"], b["units_kwh"]) for b in bills if b.get("amount_inr") and b.get("units_kwh")]
    return round(sum(a for a, _ in pairs) / sum(u for _, u in pairs), 2) if pairs else None

def run_offline(inputs: dict | None = None, today_day: int = 0, events: list | None = None,
                discom_reply: str | None = None, assumptions: dict | None = None, reply_reading: dict | None = None) -> dict:
    """reply_reading: the live Chaser agent's structured reading of discom_reply; without it, the rule-based reader is used."""
    inputs = inputs or load_sample_inputs()
    soc = inputs["society"]
    with rules.use_state(soc.get("state") or None):
        return _run(inputs, soc, today_day, events, discom_reply, assumptions, reply_reading)

def _run(inputs, soc, today_day, events, discom_reply, assumption_overrides, reply_reading=None):
    tr = Trace()
    bills, quote_list = inputs.get("bills") or [], inputs.get("quotes") or []
    a = resolve_assumptions(assumption_overrides)
    av = {k: v["value"] for k, v in a.items()}
    needs = []
    tr.note("Secretary", f"Project for {soc['name']} ({soc['flats']} flats). "
            + ("Starting with the bills." if bills else "Waiting for the common-meter bills."))

    # 1. Reader: bills -> annual kWh. Fewer than 12 months are scaled to a year and said so.
    annual = plan = rec = fair = None
    money = {}
    if bills:
        months = len(bills)
        total = sum(b["units_kwh"] for b in bills)
        annual = tr.call("Reader", "sum_bills", lambda bills: round(total * 12 / months), bills=bills)
        unclear = [b["month"] for b in bills if b.get("unclear") and not b.get("verified")]
        if unclear:
            tr.note("Reader", f"Unclear values in: {', '.join(unclear)}. Asking the committee to confirm.")
        if months < 12:
            tr.note("Reader", f"Only {months} month(s) of bills, so the year is estimated from them. Add all 12 for a firmer plan.")
            needs.append("more_bills")
    else:
        needs.append("bills")

    # 2. Sizing tools (plain code, called by the Secretary; the Planner is not an agent)
    if annual:
        plan = tr.call("Secretary", "size_system", sizing.size_system, annual_kwh=annual, flats=soc["flats"],
                       share=av["share"], yield_kwh_per_kw=av["yield_kwh_per_kw"])
        money = {o["label"]: tr.call("Secretary", "money_summary", sizing.money_summary, kw=o["kw"],
                                     cost_per_kw=av["cost_per_kw"], tariff=av["tariff"], yield_kwh_per_kw=av["yield_kwh_per_kw"])
                 for o in plan["options"]}
        rec = money["recommended"]

    # 3. Auditor: quotes
    audits, negs = [], []
    for q in quote_list:
        audit = tr.call("Auditor", "audit_quote", quotes.audit_quote, q=q)
        audits.append(audit)
        tr.note("Auditor", f"{q['vendor']}: {audit['verdict']} ({len(audit['flags'])} flag(s))")
    if not quote_list:
        needs.append("quotes")
    # 4. Simulated negotiation (plain code)
    for q, audit in zip(quote_list, audits):
        negs.append(tr.call("Secretary", "run_simulated_negotiation", negotiation.run_simulated_negotiation, quote=q, audit=audit))

    # 5. Fairness
    if rec:
        fair = tr.call("Secretary", "fairness_table", fairness.fairness_table, net_cost=rec["net_cost"],
                       saving_per_year=rec["saving_per_year"], flat_areas_sqft=inputs.get("flat_areas_sqft") or {},
                       total_flats=soc["flats"])

    # 6. Timeline + Chaser
    ev = events if events is not None else inputs.get("events", [])
    tl = tr.call("Chaser", "build_timeline", timeline.build_timeline, events=ev, today_day=today_day)
    nxt = timeline.next_action(tl)
    out_drafts = []
    if rec:
        out_drafts += [drafts.agm_notice(soc, rec["kw"], rec["total_cost"], rec["subsidy"], rec["net_cost"], rec["payback_years"],
                                         inputs.get("agm_date", "[date to be set by the committee]")),
                       drafts.agm_resolution(soc, rec["kw"], "equal")]
    for q, audit, n in zip(quote_list, audits, negs):
        if audit["verdict"] == "RED":
            out_drafts.append(drafts.proof_request(soc, q["vendor"]))
        elif n["rounds"][0]["kind"] == "request_details":
            out_drafts.append(drafts.details_request(soc, q["vendor"]))
        else:
            out_drafts.append(drafts.counter_offer(soc, q["vendor"], n["rounds"][0]["price"], n["rounds"][0]["advance_pct"], 5))
    if out_drafts:
        parts = (["AGM notice, resolution"] if rec else []) + (["vendor letters"] if quote_list else [])
        tr.note("Secretary", f"Drafted {len(out_drafts)} papers for the committee: {' and '.join(parts)}. Nothing is sent.")
    if nxt["chase_level"] == 1:
        out_drafts.append(drafts.discom_reminder(soc, nxt["label"], nxt["overdue_by"]))
        tr.note("Chaser", f"{nxt['label']} is {nxt['overdue_by']} days late. Drafted a polite reminder. Waiting for a human to approve.")
    elif nxt["chase_level"] == 2:
        out_drafts.append(drafts.discom_escalation(soc, nxt["label"], nxt["overdue_by"]))
        tr.note("Chaser", f"{nxt['label']} is {nxt['overdue_by']} days overdue. Drafted an escalation. Waiting for a human to approve.")

    # 7. Optional DISCOM reply -> replan (Plan v1 vs v2)
    plan_v2, reply_class = None, None
    if discom_reply and reply_reading:
        reply_class = {"type": reply_reading["type"], **({"max_kw": reply_reading["max_kw"]} if reply_reading.get("max_kw") else {})}
        tr.note("Chaser", f"Read the DISCOM reply with AI: {reply_reading.get('summary', reply_class['type'])}")
    elif discom_reply:
        reply_class = tr.call("Chaser", "classify_reply", replan.classify_reply, text=discom_reply)
    if discom_reply:
        if reply_class["type"] == "LOAD_LIMIT" and reply_class.get("max_kw") and annual:
            p2 = tr.call("Secretary", "replan_for_load_limit", replan.replan_for_load_limit,
                         annual_kwh=annual, flats=soc["flats"], max_kw=reply_class["max_kw"])
            m2 = sizing.money_summary(p2["recommended_kw"], cost_per_kw=av["cost_per_kw"], tariff=av["tariff"],
                                      yield_kwh_per_kw=av["yield_kwh_per_kw"])
            plan_v2 = {"reason": f"DISCOM sanctioned-load limit of {reply_class['max_kw']:.0f} kW", "plan": p2, "money": m2}

    return {
        "mode": "offline", "simulated_parts": ["vendor replies", "DISCOM replies", "clock"],
        "society": soc, "annual_kwh": annual, "bills": bills, "price_band": rules.value("price_band_per_kw"),
        "assumptions": a, "bill_average_rate": bill_average_rate(bills),
        "plan": plan, "money": money, "recommended": rec, "plan_v2": plan_v2, "reply_class": reply_class,
        "audits": audits, "negotiations": negs, "fairness": fair, "timeline": tl, "next_action": nxt,
        "drafts": out_drafts, "trace": tr.events, "today_day": today_day, "needs": needs,
        "rulebook": rules.list_rules(), "rule_coverage": rules.state_coverage(soc.get("state") or None),
    }

if __name__ == "__main__":
    print(json.dumps(run_offline(), indent=2)[:3000])
