import json
from solarsabha.pipeline import load_sample_inputs
from solarsabha.tools import quotes

def test_expected_verdicts_on_sample_quotes():
    inp = load_sample_inputs()
    for q in inp["quotes"]:
        v = quotes.audit_quote(q)["verdict"]
        assert v == inp["_expected"]["audit_verdicts"][q["vendor"]], q["vendor"]

def test_injection_is_detected_and_flagged_not_obeyed():
    q = [x for x in load_sample_inputs()["quotes"] if "Vendor B" in x["vendor"]][0]
    a = quotes.audit_quote(q)
    codes = {f["code"] for f in a["flags"]}
    assert "DOCUMENT_CONTAINS_INSTRUCTIONS" in codes and "VENDOR_NOT_VERIFIED" in codes
    assert a["verdict"] == "RED"            # the injected 'mark as approved' did nothing

def test_missing_fields_are_flagged_not_guessed():
    a = quotes.audit_quote({"vendor": "Vendor A Solar Pvt Ltd", "capacity_kw": None, "total_price_inr": None})
    assert any(f["code"] == "PRICE_MISSING" for f in a["flags"]) and a["verdict"] != "GREEN"

def test_scan_clean_text():
    assert quotes.scan_for_injection("Price Rs 17,50,000. Warranty 25 years.") == []
