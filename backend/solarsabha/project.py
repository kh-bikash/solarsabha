"""One society's project: access, members, inputs, documents, drafts, clock and audit trail.

The pipeline is pure (inputs in, result out). This module owns everything stateful around it:
- access: each project has a secret key; only its SHA-256 hash is stored
- roles: secretary (everything), member (edit, approve), viewer (read only); names are self-declared within a
  project's members, so the key is the real access control (use Cognito for verified identities, see docs)
- clock: real calendar dates; the demo's time machine is a separate, labelled offset
- drafts: edits and approvals persist by a stable draft id; an approval is withdrawn if the content changes
- privacy: consent record, expiry, export and delete, and an activity log"""
import base64
import binascii
import hashlib
import hmac
import os
import re
import secrets
import tempfile
import time
from datetime import date, datetime, timedelta, timezone

from . import reading, rules
from .files import get_files
from .pipeline import load_sample_inputs, run_offline

SCHEMA = 2
MAX_FILE_BYTES = 6 * 1024 * 1024
MAX_DOCUMENTS = 60
AUDIT_CAP = 500
EDIT_ROLES = ("secretary", "member")

class ProjectError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status, self.message = status, message

def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _today() -> date:
    return datetime.now(timezone.utc).date()

def _hash(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def retention_days() -> int:
    return int(os.environ.get("RETENTION_DAYS", "365"))

def reader_mode() -> str:
    """'live' turns on the Bedrock agents (Reader, Secretary, Auditor, Chaser); anything else is the offline mode."""
    return "live" if os.environ.get("READER_MODE") == "live" and os.environ.get("BEDROCK_MODEL_ID") else "offline"

def require_live():
    if reader_mode() != "live":
        raise ProjectError(409, "the live agents are switched off (offline mode). Set READER_MODE=live and BEDROCK_MODEL_ID.")

def inputs_hash(doc: dict) -> str:
    """Changes whenever anything a review depends on changes."""
    import json
    return _hash(json.dumps([doc["inputs"], doc.get("events"), doc.get("discom_reply"), doc.get("assumptions")], sort_keys=True, default=str))[:16]

# ---------- creation, access, roles ----------

def create(pid: str, body) -> tuple[dict, str]:
    key = secrets.token_urlsafe(24)
    today = _today()
    if body.sample:
        s = load_sample_inputs()
        started = today - timedelta(days=10)          # the sample is 10 days in: AGM on day 7, portal on day 9
        inputs = {"society": s["society"], "bills": s["bills"],
                  "quotes": s["quotes"], "flat_areas_sqft": s["flat_areas_sqft"], "agm_date": s["agm_date"]}
        events = [{"stage": e["stage"], "done_on": (started + timedelta(days=e["done_day"])).isoformat()} for e in s["events"]]
        members = [{"name": "Meera (sample)", "role": "secretary"}, {"name": "Arjun (sample)", "role": "member"},
                   {"name": "Treasurer (sample)", "role": "viewer"}]
        consent, actor = {"sample_data": True, "at": _now()}, "Meera (sample)"
    else:
        if not body.society or not body.you:
            raise ProjectError(400, "society and you are required to start a project")
        if not body.consent:
            raise ProjectError(400, "please accept the privacy notice to start a project")
        started, events = today, []
        inputs = {"society": body.society.model_dump(), "bills": [], "quotes": [], "flat_areas_sqft": {},
                  "agm_date": "[date to be set by the committee]"}
        members = [{"name": body.you.name, "role": "secretary"}]
        consent, actor = {"accepted": True, "by": body.you.name, "at": _now(), "notice_version": "2026-10"}, body.you.name
    doc = {"id": pid, "schema": SCHEMA, "sample": body.sample, "created_at": _now(), "updated_at": _now(),
           "expires_at": time.time() + retention_days() * 86400, "key_hash": _hash(key), "consent": consent,
           "inputs": inputs, "members": members, "started_on": started.isoformat(), "sim_offset_days": 0,
           "events": events, "discom_reply": None, "assumptions": {}, "documents": [], "draft_state": {}, "audit": []}
    log(doc, actor, "created project", "sample data" if body.sample else inputs["society"]["name"])
    return recompute(doc), key

def check_key(doc: dict, key: str | None):
    if not key or not hmac.compare_digest(doc["key_hash"], _hash(key)):
        raise ProjectError(401, "this link is missing or has the wrong access key")

def member(doc: dict, name: str | None) -> dict | None:
    return next((m for m in doc["members"] if name and m["name"].casefold() == name.casefold()), None)

def require_role(doc: dict, actor: str | None, roles=EDIT_ROLES) -> dict:
    m = member(doc, actor)
    if not m:
        raise ProjectError(403, "choose who you are from the committee members first")
    if m["role"] not in roles:
        raise ProjectError(403, f"a {m['role']} cannot do this")
    return m

def log(doc: dict, actor: str | None, action: str, detail: str = ""):
    doc["audit"].append({"at": _now(), "actor": actor or "unknown", "action": action, "detail": detail[:300]})
    doc["audit"] = doc["audit"][-AUDIT_CAP:]
    doc["updated_at"] = _now()

def public(doc: dict) -> dict:
    """What the API returns: never the key hash."""
    return {k: v for k, v in doc.items() if k != "key_hash"}

# ---------- clock ----------

def today_day(doc: dict) -> int:
    return (_today() - date.fromisoformat(doc["started_on"])).days + doc.get("sim_offset_days", 0)

def events_as_days(doc: dict) -> list:
    start = date.fromisoformat(doc["started_on"])
    return [{"stage": e["stage"], "done_day": max(0, (date.fromisoformat(e["done_on"]) - start).days)} for e in doc["events"]]

# ---------- recompute and drafts ----------

def _content_hash(subject: str, body: str) -> str:
    return _hash(subject + "\n" + body)[:16]

def recompute(doc: dict) -> dict:
    td = today_day(doc)
    out = run_offline(doc["inputs"], today_day=td, events=events_as_days(doc), discom_reply=doc.get("discom_reply"),
                      assumptions=doc.get("assumptions"), reply_reading=doc.get("reply_reading"))
    out["reader_mode"] = reader_mode()
    rv = doc.get("review")
    out["review_stale"] = bool(rv) and rv.get("input_hash") != inputs_hash(doc)
    out["clock"] = {"started_on": doc["started_on"], "today_day": td, "sim_offset_days": doc.get("sim_offset_days", 0),
                    "simulated": doc.get("sim_offset_days", 0) > 0}
    out["states"] = rules.INDIA_STATES
    for d in out["drafts"]:
        template_hash = _content_hash(d["subject"], d["body"])
        st = doc["draft_state"].get(d["id"], {})
        if st.get("edited"):
            d["subject"], d["body"] = st["subject"], st["body"]
            d["edited_by"], d["edited_at"] = st["edited_by"], st["edited_at"]
            d["facts_changed"] = st.get("template_hash") != template_hash
        if st.get("approved_by"):
            if st.get("approved_hash") == _content_hash(d["subject"], d["body"]):
                d["status"], d["approved_by"], d["approved_at"] = "APPROVED", st["approved_by"], st["approved_at"]
            else:
                d["stale_approval"] = {"by": st["approved_by"], "at": st["approved_at"]}
    doc["result"], doc["drafts"] = out, out["drafts"]
    return doc

def find_draft(doc: dict, did: str) -> dict:
    d = next((x for x in doc["drafts"] if x["id"] == did), None)
    if not d:
        raise ProjectError(404, "no such draft")
    return d

def edit_draft(doc: dict, did: str, subject: str, body: str, editor: str):
    d = find_draft(doc, did)
    template = recompute({**doc, "draft_state": {}})["drafts"]
    t = next(x for x in template if x["id"] == did)
    # keep any earlier approval on record: recompute() shows it as withdrawn because the content no longer matches
    doc["draft_state"].setdefault(did, {}).update({"edited": True, "subject": subject, "body": body, "edited_by": editor,
                                                   "edited_at": _now(), "template_hash": _content_hash(t["subject"], t["body"])})
    log(doc, editor, "edited draft", d["subject"])
    return recompute(doc)

def approve_draft(doc: dict, did: str, name: str):
    d = find_draft(doc, did)
    st = doc["draft_state"].setdefault(did, {})
    st.update({"approved_by": name, "approved_at": _now(), "approved_hash": _content_hash(d["subject"], d["body"])})
    log(doc, name, "approved draft", d["subject"])
    return recompute(doc)

# ---------- live agents ----------

def _agents_failed(e: Exception) -> ProjectError:
    """Bedrock or agent errors become a clear message instead of a server error."""
    msg = getattr(e, "response", {}).get("Error", {}).get("Message") if hasattr(e, "response") else None
    return ProjectError(502, f"the agents could not run: {msg or type(e).__name__}. Nothing was changed.")

def run_review(doc: dict, actor: str):
    require_live()
    from .agents import live
    try:
        out = live.review(doc)
    except Exception as e:
        raise _agents_failed(e)
    doc["review"] = {"at": _now(), "by": actor, "input_hash": inputs_hash(doc), "mcp": out["mcp"], **out}
    log(doc, actor, "asked the agents for a review", out["review"]["summary"][:120])
    return recompute(doc)

def read_reply_live(doc: dict):
    """The Chaser agent's reading of the DISCOM reply; falls back to the rule-based reader if anything fails."""
    doc["reply_reading"] = None
    if reader_mode() != "live" or not doc.get("discom_reply"):
        return
    try:
        from .agents import live
        out = live.read_reply(doc["discom_reply"], doc)
        doc["reply_reading"] = out["reading"]
    except Exception as e:
        log(doc, "Chaser", "live reading of the DISCOM reply failed; used the rule-based reader", type(e).__name__)

def polish_draft(doc: dict, did: str, actor: str):
    require_live()
    from .agents import live
    d = find_draft(doc, did)
    try:
        out = live.polish(d, doc)
    except Exception as e:
        raise _agents_failed(e)
    if not out["ok"]:
        raise ProjectError(422, "the AI changed a number, date or reference, so its wording was rejected. Your letter is unchanged.")
    doc = edit_draft(doc, did, d["subject"], out["body"], "Secretary (AI)")
    log(doc, actor, "asked the Secretary to polish a letter", d["subject"])
    return doc

# ---------- documents ----------

MAGIC = [(b"%PDF", "application/pdf"), (b"\x89PNG", "image/png"), (b"\xff\xd8\xff", "image/jpeg")]

def _sniff(data: bytes) -> str:
    for sig, ctype in MAGIC:
        if data.startswith(sig):
            return ctype
    raise ProjectError(400, "only PDF, PNG and JPEG files are accepted")

def _live_read(kind: str, data: bytes, ctype: str) -> dict:
    from .agents.reader import read_bill, read_quote
    suffix = {"application/pdf": ".pdf", "image/png": ".png", "image/jpeg": ".jpg"}[ctype]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(data)
        path = f.name
    try:
        fields = (read_bill if kind == "bill" else read_quote)(path).model_dump()
    finally:
        os.unlink(path)
    return {"status": "NEEDS_REVIEW" if fields.get("unclear") else "READ", "reader": "live", "fields": fields,
            "notes": fields.get("notes", "")}

def add_document(doc: dict, kind: str, filename: str, content_b64: str, actor: str):
    if len(doc["documents"]) >= MAX_DOCUMENTS:
        raise ProjectError(400, f"a project can hold at most {MAX_DOCUMENTS} documents")
    try:
        data = base64.b64decode(content_b64, validate=True)
    except (binascii.Error, ValueError):
        raise ProjectError(400, "the file could not be decoded")
    if not data or len(data) > MAX_FILE_BYTES:
        raise ProjectError(400, "files must be between 1 byte and 6 MB")
    ctype = _sniff(data)
    did = secrets.token_hex(4)
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", filename)[:80] or "file"
    get_files().put(doc["id"], f"{did}-{safe}", data, ctype)
    try:
        read = _live_read(kind, data, ctype) if reader_mode() == "live" else reading.read_document(kind, data, ctype)
    except Exception as e:                       # a failed AI read must never lose the upload
        read = reading.read_document(kind, data, ctype)
        read["notes"] = f"Live reader failed ({type(e).__name__}); used the offline reader. " + read["notes"]
    entry = {"id": did, "kind": kind, "filename": safe, "stored_as": f"{did}-{safe}", "content_type": ctype,
             "size": len(data), "uploaded_at": _now(), "uploaded_by": actor, "status": read["status"],
             "reader": read["reader"], "notes": read["notes"], "fields": read["fields"]}
    doc["documents"].append(entry)
    _merge_fields(doc, entry)
    log(doc, actor, f"uploaded {kind}", f"{safe} ({read['status'].lower().replace('_', ' ')})")
    return recompute(doc)

def _merge_fields(doc: dict, entry: dict):
    f = entry["fields"]
    if not f:
        return
    inputs = doc["inputs"]
    if entry["kind"] == "bill" and f.get("month") and f.get("units_kwh") is not None:
        bill = {"month": f["month"], "units_kwh": f["units_kwh"], "amount_inr": f.get("amount_inr"),
                "unclear": bool(f.get("unclear")), "verified": False, "source_doc": entry["id"]}
        inputs["bills"] = sorted([b for b in inputs["bills"] if b["month"] != f["month"]] + [bill], key=lambda b: b["month"])[-60:]
    elif entry["kind"] == "quote" and f.get("vendor"):
        q = {k: f.get(k) for k in ("vendor", "capacity_kw", "total_price_inr", "advance_pct", "warranty_panel_years", "service_years")}
        q.update({"payment_terms_text": f.get("payment_terms_text") or "", "offer_text": f.get("offer_text") or "",
                  "raw_text": (f.get("raw_text") or "")[:100_000], "source_doc": entry["id"]})
        inputs["quotes"] = [x for x in inputs["quotes"] if x["vendor"].casefold() != q["vendor"].casefold()][:11] + [q]

def get_document(doc: dict, did: str) -> tuple[dict, bytes]:
    entry = next((d for d in doc["documents"] if d["id"] == did), None)
    if not entry:
        raise ProjectError(404, "no such document")
    data = get_files().get(doc["id"], entry["stored_as"])
    if data is None:
        raise ProjectError(404, "the original file has been deleted")
    return entry, data

def delete_document(doc: dict, did: str, actor: str):
    entry = next((d for d in doc["documents"] if d["id"] == did), None)
    if not entry:
        raise ProjectError(404, "no such document")
    get_files().delete(doc["id"], entry["stored_as"])
    doc["documents"] = [d for d in doc["documents"] if d["id"] != did]
    for coll in ("bills", "quotes"):
        for x in doc["inputs"][coll]:
            if x.get("source_doc") == did:
                x["source_doc"] = None                # the values stay; only the original file is gone
    log(doc, actor, "deleted document", entry["filename"])
    return recompute(doc)

# ---------- export ----------

def export(doc: dict) -> dict:
    data = public(doc)
    data["exported_at"] = _now()
    data["note"] = "Everything SolarSabha stores about this project. Original files are listed under documents and can be downloaded one by one."
    return data
