"""Run the whole product loop with NO AWS and NO LLM. Good first thing for every teammate to run.
Usage: python scripts/demo_offline.py [--day 50] [--reply]"""
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from solarsabha.pipeline import run_offline, load_sample_inputs

ap = argparse.ArgumentParser(); ap.add_argument("--day", type=int, default=0); ap.add_argument("--reply", action="store_true")
a = ap.parse_args()
i = load_sample_inputs()
r = run_offline(i, today_day=a.day, discom_reply=i["discom_reply_example"] if a.reply else None)
rec = r["recommended"]
print(f"\n{r['society']['name']}: common-area use {r['annual_kwh']:,} kWh/year")
print(f"Recommended: {rec['kw']} kW | cost Rs {rec['total_cost']:,.0f} | subsidy Rs {rec['subsidy']:,.0f} | net Rs {rec['net_cost']:,.0f}")
print(f"Saving Rs {rec['saving_per_year']:,.0f}/yr | payback {rec['payback_years']} yrs | CO2 avoided {rec['co2_tonnes_year']} t/yr")
print("\nQuote audit:")
for au in r["audits"]:
    print(f"  {au['verdict']:5} {au['vendor']}  (Rs {au['price_per_kw']:,}/kW)")
    for f in au["flags"]: print(f"        - [{f['level']}] {f['message']}")
print("\nTimeline (day %d):" % a.day)
for s in r["timeline"]: print(f"  {s['status']:8} {s['label']}")
print("Next action:", r["next_action"])
if r["plan_v2"]: print(f"\nDISCOM reply -> Plan v2: {r['plan_v2']['plan']['recommended_kw']} kW ({r['plan_v2']['reason']})")
print("\nDrafts (all DRAFT, nothing is sent):", [d["kind"] for d in r["drafts"]])
print("\nSimulated in this run:", ", ".join(r["simulated_parts"]))
