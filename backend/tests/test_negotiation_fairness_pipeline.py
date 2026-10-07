from solarsabha.pipeline import run_offline, load_sample_inputs
from solarsabha.tools import negotiation, quotes, fairness

def test_red_vendor_is_not_negotiated_with():
    q = [x for x in load_sample_inputs()["quotes"] if "Vendor B" in x["vendor"]][0]
    n = negotiation.run_simulated_negotiation(q, quotes.audit_quote(q))
    assert n["skipped"] and n["rounds"][0]["kind"] == "request_proof" and n["simulated"] is True

def test_negotiation_never_goes_below_vendor_floor_and_is_labelled():
    q = load_sample_inputs()["quotes"][0]
    n = negotiation.run_simulated_negotiation(q, quotes.audit_quote(q))
    assert n["simulated"] and n["final_price"] >= q["total_price_inr"] * 0.92 - 1

def test_fairness_totals_add_up():
    t = fairness.fairness_table(1_152_000, 352_800, {"A": 900, "B": 1100})
    assert abs(sum(r["area_cost"] for r in t["flats"]) - 1_152_000) <= 2

def test_fairness_splits_across_whole_society_not_just_listed_flats():
    t = fairness.fairness_table(1_152_000, 352_800, {"A": 900, "B": 1100}, total_flats=50)
    assert t["flats"][0]["equal_cost"] == 23_040 and "2 of 50" in t["note"]
    r = run_offline(load_sample_inputs())
    assert r["fairness"]["flats"][0]["equal_cost"] * r["society"]["flats"] == r["money"]["recommended"]["net_cost"]

def test_pipeline_end_to_end_and_no_send_capability():
    i = load_sample_inputs()
    r = run_offline(i, today_day=50, discom_reply=i["discom_reply_example"])
    assert r["annual_kwh"] == i["_expected"]["annual_kwh"] and r["plan"]["recommended_kw"] == i["_expected"]["recommended_kw"]
    assert r["plan_v2"]["plan"]["recommended_kw"] == 25
    assert all(d["status"] == "DRAFT" for d in r["drafts"])
    assert any(d["kind"] == "discom_escalation" for d in r["drafts"])
    assert r["simulated_parts"]
