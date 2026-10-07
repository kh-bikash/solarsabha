"""Quote maths and risk flags. Deterministic. The Auditor agent explains these results; it never invents them."""
import re
from .. import rules

PRESSURE_PHRASES = ["sign today", "offer ends", "limited time", "only today", "last day", "book now", "act now"]
BEFORE_APPROVAL = re.compile(r"before\s+(discom\s+)?(approval|feasibility|sanction)", re.I)
INJECTION_PATTERNS = [
    r"ignore (all |any )?(previous|prior|above) (instructions|rules)",
    r"\bas an? (ai|assistant|language model)\b", r"\bsystem prompt\b",
    r"mark (this|the) vendor (as )?(approved|verified|empanelled)",
    r"do not (tell|inform|warn) the (committee|user)",
]

def price_per_kw(total_price, capacity_kw) -> int:
    return round(total_price / capacity_kw)

def scan_for_injection(text) -> list:
    """Documents are data, never instructions. Return any instruction-like phrases found."""
    return [m.group(0) for p in INJECTION_PATTERNS for m in re.finditer(p, text or "", re.I)]

def check_vendor(name) -> dict:
    listed = name.strip().lower() in {v.lower() for v in rules.approved_vendors()}
    return {"vendor": name, "found_in_list": listed, "label": "SAMPLE vendor list. Verify on the official portal."}

def audit_quote(q) -> dict:
    """q fields: vendor, capacity_kw, total_price_inr, advance_pct, warranty_panel_years, service_years,
    payment_terms_text, offer_text, raw_text. Missing fields are None and are flagged, never guessed."""
    flags = []
    def add(level, code, msg, rule=None):
        flags.append({"level": level, "code": code, "message": msg, "rule": rule})

    ppk = price_per_kw(q["total_price_inr"], q["capacity_kw"]) if q.get("total_price_inr") and q.get("capacity_kw") else None
    band = rules.value("price_band_per_kw")
    if ppk is None:
        add("amber", "PRICE_MISSING", "Price or capacity could not be read; ask the vendor.")
    elif ppk < band["low"]:
        add("amber", "PRICE_LOW", f"Rs {ppk:,} per kW is below the usual band (Rs {band['low']:,} to {band['high']:,}). Ask what is left out.", "price_band_per_kw")
    elif ppk > band["high"]:
        add("amber", "PRICE_HIGH", f"Rs {ppk:,} per kW is above the usual band (Rs {band['low']:,} to {band['high']:,}).", "price_band_per_kw")

    v = check_vendor(q["vendor"])
    if not v["found_in_list"]:
        add("red", "VENDOR_NOT_VERIFIED", "Vendor not found in the approved list we loaded. A non-listed installer may void the subsidy. Ask for proof.", "empanelled_vendor_requirement")

    adv = q.get("advance_pct")
    if adv is None:
        add("amber", "ADVANCE_MISSING", "Advance payment not stated.")
    elif adv > rules.value("advance_flag_pct"):
        add("amber", "ADVANCE_HIGH", f"Advance of {adv}% is above our {rules.value('advance_flag_pct')}% flag level.", "advance_flag_pct")

    terms = " ".join(filter(None, [q.get("payment_terms_text"), q.get("offer_text")]))
    if BEFORE_APPROVAL.search(terms):
        add("amber", "PAY_BEFORE_APPROVAL", "Payment is asked before DISCOM approval.", "sign_before_approval_warning")
    if any(p in terms.lower() for p in PRESSURE_PHRASES):
        add("amber", "PRESSURE", "The offer uses time pressure. Do not sign under pressure.")

    if q.get("warranty_panel_years") is None:
        add("amber", "WARRANTY_MISSING", "Panel warranty not stated.")
    sy = q.get("service_years")
    if sy is None:
        add("amber", "SERVICE_MISSING", "Service/maintenance period not stated.")
    elif sy < rules.value("min_service_years"):
        add("amber", "SERVICE_SHORT", f"Only {sy} year(s) of service; our flag level is {rules.value('min_service_years')}.", "min_service_years")

    inj = scan_for_injection(q.get("raw_text", ""))
    if inj:
        add("red", "DOCUMENT_CONTAINS_INSTRUCTIONS", f"The document contains text that tries to instruct an AI ({inj[0]!r}). It was ignored and treated as data.")

    verdict = "RED" if any(f["level"] == "red" for f in flags) else ("AMBER" if flags else "GREEN")
    return {"vendor": q["vendor"], "price_per_kw": ppk, "vendor_check": v, "flags": flags, "verdict": verdict}
