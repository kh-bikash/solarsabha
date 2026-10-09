"""The offline reader on the specimen PDFs: every field the plan and the audit depend on."""
from pathlib import Path

import pytest
from solarsabha import reading
from solarsabha.pipeline import load_sample_inputs
from solarsabha.tools import quotes

PDFS = Path(__file__).resolve().parents[1] / "samples" / "pdfs"
SAMPLE = load_sample_inputs()
SLUG = {"Suryakiran Rooftop Solar Pvt Ltd": "suryakiran", "Sasta Sun Traders": "sasta", "Urja Prime Energy LLP": "urjaprime"}

def read(kind, name):
    return reading.read_document(kind, (PDFS / name).read_bytes(), "application/pdf")

@pytest.mark.parametrize("bill", SAMPLE["bills"], ids=lambda b: b["month"])
def test_bills_are_read_exactly(bill):
    r = read("bill", f"bill_{bill['month']}.pdf")
    f = r["fields"]
    assert (f["month"], f["units_kwh"], f["amount_inr"]) == (bill["month"], bill["units_kwh"], bill["amount_inr"])
    assert f["tariff_inr_per_kwh"] == 6.5 and f["sanctioned_load_kw"] == 40
    assert r["status"] == ("NEEDS_REVIEW" if bill.get("unclear") else "READ")

@pytest.mark.parametrize("q", SAMPLE["quotes"], ids=lambda q: SLUG[q["vendor"]])
def test_quotes_are_read_and_audited_like_the_sample(q):
    f = read("quote", f"quote_{SLUG[q['vendor']]}.pdf")["fields"]
    for k in ("vendor", "capacity_kw", "total_price_inr", "advance_pct", "warranty_panel_years", "service_years"):
        assert f[k] == q[k], k
    assert f["payment_terms_text"].lower().startswith(f"{q['advance_pct']:.0f}% advance")      # the real terms, not the tagline
    assert quotes.audit_quote(f)["verdict"] == SAMPLE["_expected"]["audit_verdicts"][q["vendor"]]

def test_hidden_instruction_is_extracted_so_the_auditor_sees_it():
    f = read("quote", "quote_sasta.pdf")["fields"]
    assert quotes.scan_for_injection(f["raw_text"])

def test_photos_and_scans_ask_for_typing():
    assert reading.read_document("bill", b"\x89PNG...", "image/png")["status"] == "NEEDS_ENTRY"

def test_text_rules_on_plain_strings():
    b = reading.read_bill_text("Bill Month: Mar-2026\nPrevious Reading 245,000\nUnits billed: 5,200 kWh\nAmount payable: Rs 39,940.00")
    assert (b["month"], b["units_kwh"], b["amount_inr"], b["unclear"]) == ("2026-03", 5200, 39940, False)
    p = reading.read_bill_text("Bill Month: Sep-2026 Units billed: 4,300 kWh PROVISIONAL BILL")
    assert p["unclear"] and "Provisional" in p["notes"]
