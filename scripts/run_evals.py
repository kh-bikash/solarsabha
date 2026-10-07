"""Accuracy scoreboard. `--mode offline` checks the deterministic tools against known answers (always runs).
`--mode live` also runs the Reader on the sample PDFs and compares with the expected values (needs Bedrock).
Show the printed score in the demo video."""
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from solarsabha.pipeline import load_sample_inputs
from solarsabha.tools import quotes, sizing

ap = argparse.ArgumentParser(); ap.add_argument("--mode", choices=["offline", "live"], default="offline"); a = ap.parse_args()
inp = load_sample_inputs(); ok = total = 0
def check(name, cond):
    global ok, total
    total += 1; ok += bool(cond); print(("PASS " if cond else "FAIL ") + name)

for q in inp["quotes"]:
    check(f"audit verdict {q['vendor']}", quotes.audit_quote(q)["verdict"] == inp["_expected"]["audit_verdicts"][q["vendor"]])
check("prompt-injection in Vendor B is detected", bool(quotes.scan_for_injection(inp["quotes"][1]["raw_text"])))
check("recommended size", sizing.size_system(inp["_expected"]["annual_kwh"], inp["society"]["flats"])["recommended_kw"] == inp["_expected"]["recommended_kw"])

if a.mode == "live":
    from solarsabha.agents.reader import read_bill, read_quote
    pdfs = ROOT / "backend/samples/pdfs"
    for b in inp["bills"]:
        got = read_bill(str(pdfs / f"bill_{b['month']}.pdf"))
        check(f"read bill {b['month']}", got.units_kwh == b["units_kwh"])
    for q in inp["quotes"]:
        got = read_quote(str(pdfs / f"quote_vendor_{q['vendor'].split()[1].lower()}.pdf"))
        check(f"read quote price {q['vendor']}", got.total_price_inr == q["total_price_inr"])
print(f"\nSCORE: {ok}/{total}")
sys.exit(0 if ok == total else 1)
