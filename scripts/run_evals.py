"""Accuracy scoreboard. Show the printed score in the demo video.

--mode offline (default, no AWS): the plain-code tools against known answers, and the offline text reader on all
               18 specimen PDFs (12 bills, 3 demo quotations, 3 evaluation quotations: 2 green, 2 amber, 2 red in all).
--mode live    also runs the Bedrock Reader agent on the same PDFs (needs BEDROCK_MODEL_ID and model access)."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from solarsabha import reading
from solarsabha.pipeline import load_sample_inputs
from solarsabha.tools import quotes, sizing

ap = argparse.ArgumentParser(); ap.add_argument("--mode", choices=["offline", "live"], default="offline"); a = ap.parse_args()
inp = load_sample_inputs(); ok = total = 0
PDFS = ROOT / "backend/samples/pdfs"
SLUG = {"Suryakiran Rooftop Solar Pvt Ltd": "suryakiran", "Sasta Sun Traders": "sasta", "Urja Prime Energy LLP": "urjaprime"}
EVAL = json.loads((ROOT / "backend/samples/eval_quotes.json").read_text(encoding="utf-8"))["quotes"]
QUOTE_FIELDS = ["capacity_kw", "total_price_inr", "advance_pct", "warranty_panel_years", "service_years"]

def check(name, cond):
    global ok, total
    total += 1; ok += bool(cond); print(("PASS " if cond else "FAIL ") + name)

print("-- plain-code tools --")
for q in inp["quotes"]:
    check(f"audit verdict {q['vendor']}", quotes.audit_quote(q)["verdict"] == inp["_expected"]["audit_verdicts"][q["vendor"]])
check("prompt injection in the Sasta Sun Traders quote is detected", bool(quotes.scan_for_injection(inp["quotes"][1]["raw_text"])))
check("recommended size", sizing.size_system(inp["_expected"]["annual_kwh"], inp["society"]["flats"])["recommended_kw"] == inp["_expected"]["recommended_kw"])

def score_reader(label, read_bill, read_quote):
    print(f"-- {label} reader on specimen PDFs --")
    for b in inp["bills"]:
        got = read_bill(PDFS / f"bill_{b['month']}.pdf")
        check(f"{label}: bill {b['month']} units and amount",
              got.get("units_kwh") == b["units_kwh"] and got.get("amount_inr") == b["amount_inr"])
        if b.get("unclear"):
            check(f"{label}: bill {b['month']} flagged as unclear (provisional)", bool(got.get("unclear")))
    for q in inp["quotes"]:
        got = read_quote(PDFS / f"quote_{SLUG[q['vendor']]}.pdf")
        check(f"{label}: quote {q['vendor']} fields", all(got.get(k) == q.get(k) for k in QUOTE_FIELDS))
        check(f"{label}: quote {q['vendor']} verdict from the PDF",
              quotes.audit_quote({**got, "vendor": q["vendor"]})["verdict"] == inp["_expected"]["audit_verdicts"][q["vendor"]])

    for q in EVAL:
        got = read_quote(PDFS / f"quote_{q['slug']}.pdf")
        audit = quotes.audit_quote({**got, "vendor": q["vendor"]})
        check(f"{label}: eval quote {q['vendor']} fields", all(got.get(k) == q.get(k) for k in QUOTE_FIELDS))
        check(f"{label}: eval quote {q['vendor']} verdict {q['expected_verdict']} with the expected flags",
              audit["verdict"] == q["expected_verdict"] and sorted(f["code"] for f in audit["flags"]) == sorted(q["expected_flags"]))

def offline(kind):
    return lambda p: reading.read_document(kind, p.read_bytes(), "application/pdf")["fields"]

score_reader("offline", offline("bill"), offline("quote"))
if a.mode == "live":
    from solarsabha.agents.reader import read_bill, read_quote
    score_reader("live", lambda p: read_bill(str(p)).model_dump(), lambda p: read_quote(str(p)).model_dump())
print(f"\nSCORE: {ok}/{total}")
sys.exit(0 if ok == total else 1)
