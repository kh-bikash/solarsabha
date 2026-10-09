"""The offline reader: pull bill and quote fields out of digital (text) PDFs with plain rules, no AI.

Used when the live Reader agent is not available. It only reads text that is really in the PDF; photos and
scanned PDFs have no text layer, so they come back marked unclear for the committee to type in. Anything the
rules cannot find is None and flagged, never guessed. Hidden text (like an instruction aimed at an AI) is still
extracted, so the Auditor's injection scan sees it."""
import io
import re

MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
NUM = r"(\d[\d,]*(?:\.\d+)?)"

def pdf_text(data: bytes) -> str:
    """All text in a PDF, pages joined. Empty string if the PDF has no text layer."""
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages).strip()

def _num(s):
    return float(s.replace(",", "")) if s is not None else None

def _first(pattern, text, flags=re.I):
    m = re.search(pattern, text, flags)
    return m.group(1) if m else None

PROVISIONAL = re.compile(r"provisional|reading not available|\bRNA\b|average consumption|estimated (?:reading|units)", re.I)

def _month(text):
    m = re.search(r"bill(?:ing)?\s*month\s*:?\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,.-]+(20\d{2})", text, re.I)
    if m:
        return f"{m.group(2)}-{MONTHS[m.group(1).lower()]:02d}"
    m = re.search(r"\b(20\d{2})-(0[1-9]|1[0-2])\b", text)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    m = re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,.-]+(20\d{2})\b", text, re.I)
    if m:
        return f"{m.group(2)}-{MONTHS[m.group(1).lower()]:02d}"
    return None

def read_bill_text(text: str) -> dict:
    # a number counts as consumption only when 'kWh' follows it, so meter readings are never mistaken for units
    units = _first(rf"(?:units?\s*(?:consumed|billed)|consumption)\s*(?:\(kwh\))?\s*:?\s*{NUM}\s*(?:kwh|units)", text) \
        or _first(rf"{NUM}\s*kwh\b", text)
    amount = _first(rf"(?:amount\s*payable|net\s*payable|total\s*(?:amount|payable)|bill\s*amount)\D{{0,20}}(?:rs\.?|inr|₹)?\s*{NUM}", text)
    tariff = _first(rf"(?:tariff|rate)\D{{0,20}}(?:rs\.?|inr|₹)?\s*{NUM}\s*(?:/|per)\s*(?:kwh|unit)", text)
    load = _first(rf"sanctioned\s*load\D{{0,20}}{NUM}\s*kw", text)
    out = {"month": _month(text), "units_kwh": _num(units), "amount_inr": _num(amount),
           "tariff_inr_per_kwh": _num(tariff), "sanctioned_load_kw": _num(load)}
    missing = [k for k in ("month", "units_kwh") if out[k] is None]
    notes = [f"Could not find: {', '.join(missing)}."] if missing else []
    if PROVISIONAL.search(text):
        notes.append("Provisional bill: the meter was not read, so these units are an estimate. Confirm with the next actual reading.")
    out["unclear"] = bool(notes)
    out["notes"] = " ".join(notes)
    return out

def read_quote_text(text: str) -> dict:
    first_line = next((ln for ln in text.splitlines() if ln.strip()), "")
    vendor = re.split(r"\s*\|\s*|\s+quotation\b|\s+quote\b", first_line, maxsplit=1, flags=re.I)[0].strip() or None
    capacity = _first(rf"(?:for|capacity|system\s*size)\D{{0,10}}{NUM}\s*kwp?\b", text) or _first(rf"{NUM}\s*kwp?\b", text)
    price = _first(rf"(?:grand\s*total|total\s*amount|total\s*price|total\s*cost|net\s*payable)[^0-9]{{0,40}}?(?:rs\.?|inr|₹)\s*{NUM}", text) \
        or _first(rf"(?:price|total|amount|cost)\D{{0,15}}(?:rs\.?|inr|₹)\s*{NUM}", text) or _first(rf"(?:rs\.?|inr|₹)\s*{NUM}", text)
    advance = _first(rf"{NUM}\s*%\s*advance", text) or _first(rf"advance\D{{0,15}}{NUM}\s*%", text)
    warranty = _first(rf"(?:panel\s*)?warranty\D{{0,15}}{NUM}\s*(?:years?|yrs?)", text)
    service = _first(rf"(?:service|maintenance|amc|o\s*&\s*m)\D{{0,15}}{NUM}\s*(?:years?|yrs?)", text)
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n", text) if s.strip()]
    terms = " ".join(s for s in sentences if re.search(r"advance|payment|pay\b|instal", s, re.I))
    offer = " ".join(s for s in sentences if re.search(r"sign today|offer ends|limited time|only today|last day|book now|act now", s, re.I))
    out = {"vendor": vendor, "capacity_kw": _num(capacity), "total_price_inr": _num(price), "advance_pct": _num(advance),
           "warranty_panel_years": _num(warranty), "service_years": _num(service),
           "payment_terms_text": terms, "offer_text": offer, "raw_text": text}
    missing = [k for k in ("vendor", "capacity_kw", "total_price_inr") if out[k] is None]
    out["unclear"] = bool(missing)
    out["notes"] = f"Could not find: {', '.join(missing)}." if missing else ""
    return out

def read_document(kind: str, data: bytes, content_type: str) -> dict:
    """Offline read of one uploaded file. Returns the fields plus a status for the UI."""
    if content_type != "application/pdf":
        return {"status": "NEEDS_ENTRY", "reader": "offline", "fields": None,
                "notes": "Photos need the live Reader (AI). Please type the values in for now."}
    text = pdf_text(data)
    if not text:
        return {"status": "NEEDS_ENTRY", "reader": "offline", "fields": None,
                "notes": "This PDF has no text layer (probably a scan). Please type the values in."}
    fields = read_bill_text(text) if kind == "bill" else read_quote_text(text)
    return {"status": "NEEDS_REVIEW" if fields["unclear"] else "READ", "reader": "offline", "fields": fields, "notes": fields["notes"]}
