"""One Lambda behind API Gateway (HTTP API, payload v2). Also used by scripts/dev_server.py for local development.

Every /projects/{id} route needs the header `x-project-key` (returned once when the project is created).
Routes that change anything also need `x-actor`: the name of a committee member allowed to do it.

  GET    /health                              liveness
  GET    /rules                               the rulebook and the list of states
  POST   /projects                            {"sample": true} or {"society": {...}, "you": {...}, "consent": true}
  GET    /projects/{id}                       current state
  DELETE /projects/{id}                       {"confirm_name": "<society name>"}   secretary only
  GET    /projects/{id}/export                everything stored, as JSON
  PUT    /projects/{id}/society | bills | quotes | flats | assumptions | events
  PUT    /projects/{id}/members               secretary only
  POST   /projects/{id}/documents             {"kind": "bill"|"quote", "filename", "content_base64"}
  GET    /projects/{id}/documents/{did}       the original file
  DELETE /projects/{id}/documents/{did}
  POST   /projects/{id}/advance               {"days": N}   SIMULATED clock (demo time machine)
  POST   /projects/{id}/clock/reset           back to the real date
  POST   /projects/{id}/discom-reply          {"text": "..."}   a DISCOM email pasted in
  DELETE /projects/{id}/discom-reply
  PUT    /projects/{id}/drafts/{did}          {"subject", "body", "editor"}
  POST   /projects/{id}/drafts/{did}/approve  {"name": "<member>"}   (nothing is sent in this build)
  GET    /projects/{id}/drafts/{did}/docx     Word download
  POST   /projects/{id}/review                live mode: the Secretary calls the Auditor and Chaser and reports
  POST   /projects/{id}/drafts/{did}/polish   live mode: AI rewording; rejected if any number, date or reference changes
"""
import base64
import json
import logging
import os
import re
import time
import uuid
from urllib.parse import unquote

from pydantic import ValidationError

from .. import alarm
from .. import project as P
from .. import rules, schemas as S
from ..export import draft_docx, draft_filename
from ..files import get_files
from ..state import get_store, new_id

log = logging.getLogger("solarsabha.api")
if not log.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(h)
    log.setLevel(logging.INFO)

MAX_BODY_BYTES = 9_000_000

def _headers(extra: dict | None = None) -> dict:
    return {"content-type": "application/json",
            "access-control-allow-origin": os.environ.get("ALLOWED_ORIGIN", "*"),
            "access-control-allow-headers": "content-type,x-project-key,x-actor",
            "access-control-allow-methods": "GET,POST,PUT,DELETE,OPTIONS",
            "access-control-expose-headers": "content-disposition",
            "x-content-type-options": "nosniff", "cache-control": "no-store", **(extra or {})}

def _resp(code: int, body) -> dict:
    return {"statusCode": code, "headers": _headers(), "body": json.dumps(body, default=str)}

def _file(data: bytes, ctype: str, filename: str) -> dict:
    return {"statusCode": 200, "isBase64Encoded": True, "body": base64.b64encode(data).decode(),
            "headers": _headers({"content-type": ctype, "content-disposition": f'attachment; filename="{filename}"'})}

def _parse(event: dict, model):
    raw = event.get("body") or ""
    if event.get("isBase64Encoded") and raw:
        raw = base64.b64decode(raw).decode()
    if len(raw) > MAX_BODY_BYTES:
        raise P.ProjectError(413, "request too large")
    try:
        return model.model_validate(json.loads(raw) if raw else {})
    except json.JSONDecodeError:
        raise P.ProjectError(400, "the request body is not valid JSON")
    except ValidationError as e:
        problems = "; ".join(f"{'.'.join(str(x) for x in err['loc']) or 'body'}: {err['msg']}" for err in e.errors()[:8])
        raise P.ProjectError(400, problems)

def _header(event: dict, name: str) -> str | None:
    hs = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    v = hs.get(name)
    return unquote(v) if v else None

# ---------- project routes: (method, sub-path pattern, handler, who may call) ----------
# who: "read" = anyone with the key; "edit" = secretary or member; "secretary" = secretary only

def _save(store, doc):
    doc["alarm_at"] = alarm.sync(doc)               # the Chaser's next wake-up (AWS only)
    store.put(doc["id"], doc)
    return _resp(200, P.public(doc))

def r_get(ev, store, doc, actor, m):
    return _resp(200, P.public(doc))

def r_delete(ev, store, doc, actor, m):
    b = _parse(ev, S.DeleteProject)
    if b.confirm_name.casefold() != doc["inputs"]["society"]["name"].casefold():
        raise P.ProjectError(400, "type the society name exactly to confirm deletion")
    get_files().delete_project(doc["id"])
    alarm.remove(doc["id"])
    store.delete(doc["id"])
    log.info(json.dumps({"event": "project_deleted", "project": doc["id"]}))
    return _resp(200, {"deleted": True})

def r_export(ev, store, doc, actor, m):
    return _resp(200, P.export(doc))

def r_society(ev, store, doc, actor, m):
    b = _parse(ev, S.Society)
    doc["inputs"]["society"] = b.model_dump()
    P.log(doc, actor, "updated society details", b.name)
    return _save(store, P.recompute(doc))

def r_bills(ev, store, doc, actor, m):
    b = _parse(ev, S.Bills)
    doc["inputs"]["bills"] = sorted([x.model_dump() for x in b.bills], key=lambda x: x["month"])
    P.log(doc, actor, "updated bills", f"{len(b.bills)} month(s)")
    return _save(store, P.recompute(doc))

def r_quotes(ev, store, doc, actor, m):
    b = _parse(ev, S.Quotes)
    doc["inputs"]["quotes"] = [x.model_dump() for x in b.quotes]
    P.log(doc, actor, "updated quotes", f"{len(b.quotes)} quote(s)")
    return _save(store, P.recompute(doc))

def r_flats(ev, store, doc, actor, m):
    b = _parse(ev, S.Flats)
    if len(b.flat_areas_sqft) > doc["inputs"]["society"]["flats"]:
        raise P.ProjectError(400, "more flats listed than the society has")
    doc["inputs"]["flat_areas_sqft"] = b.flat_areas_sqft
    P.log(doc, actor, "updated flat areas", f"{len(b.flat_areas_sqft)} flat(s)")
    return _save(store, P.recompute(doc))

def r_assumptions(ev, store, doc, actor, m):
    b = _parse(ev, S.Assumptions)
    doc["assumptions"] = {k: v for k, v in b.model_dump().items() if v is not None}
    P.log(doc, actor, "changed assumptions", ", ".join(f"{k}={v}" for k, v in doc["assumptions"].items()) or "reset to rulebook")
    return _save(store, P.recompute(doc))

def r_events(ev, store, doc, actor, m):
    b = _parse(ev, S.Events)
    start, latest = P.date.fromisoformat(doc["started_on"]), P._today() + P.timedelta(days=doc.get("sim_offset_days", 0))
    for e in b.events:
        if not (start <= e.done_on <= latest):
            raise P.ProjectError(400, f"{e.stage}: the date must be between the project start ({start}) and today")
    doc["events"] = [{"stage": e.stage, "done_on": e.done_on.isoformat()} for e in b.events]
    P.log(doc, actor, "recorded progress", ", ".join(f"{e.stage} on {e.done_on}" for e in b.events) or "cleared")
    return _save(store, P.recompute(doc))

def r_members(ev, store, doc, actor, m):
    b = _parse(ev, S.Members)
    names = [x.name.casefold() for x in b.members]
    if len(names) != len(set(names)):
        raise P.ProjectError(400, "member names must be unique")
    doc["members"] = [x.model_dump() for x in b.members]
    P.log(doc, actor, "updated members", ", ".join(f"{x.name} ({x.role})" for x in b.members))
    return _save(store, P.recompute(doc))

def r_upload(ev, store, doc, actor, m):
    b = _parse(ev, S.Upload)
    return _save(store, P.add_document(doc, b.kind, b.filename, b.content_base64, actor))

def r_doc_get(ev, store, doc, actor, m):
    entry, data = P.get_document(doc, m.group(1))
    return _file(data, entry["content_type"], entry["filename"])

def r_doc_delete(ev, store, doc, actor, m):
    return _save(store, P.delete_document(doc, m.group(1), actor))

def r_advance(ev, store, doc, actor, m):
    b = _parse(ev, S.Advance)
    doc["sim_offset_days"] = doc.get("sim_offset_days", 0) + b.days
    P.log(doc, actor, "moved the simulated clock", f"+{b.days} days")
    return _save(store, P.recompute(doc))

def r_clock_reset(ev, store, doc, actor, m):
    doc["sim_offset_days"] = 0
    P.log(doc, actor, "reset the clock to today")
    return _save(store, P.recompute(doc))

def r_reply(ev, store, doc, actor, m):
    b = _parse(ev, S.DiscomReply)
    doc["discom_reply"] = b.text
    P.read_reply_live(doc)
    P.log(doc, actor, "added a DISCOM reply", b.text[:80])
    return _save(store, P.recompute(doc))

def r_reply_clear(ev, store, doc, actor, m):
    doc["discom_reply"], doc["reply_reading"] = None, None
    P.log(doc, actor, "removed the DISCOM reply")
    return _save(store, P.recompute(doc))

def r_draft_edit(ev, store, doc, actor, m):
    b = _parse(ev, S.DraftEdit)
    P.require_role(doc, b.editor)
    return _save(store, P.edit_draft(doc, m.group(1), b.subject, b.body, b.editor))

def r_draft_approve(ev, store, doc, actor, m):
    b = _parse(ev, S.Approve)
    P.require_role(doc, b.name)
    return _save(store, P.approve_draft(doc, m.group(1), P.member(doc, b.name)["name"]))

def r_review(ev, store, doc, actor, m):
    return _save(store, P.run_review(doc, actor))

def r_draft_polish(ev, store, doc, actor, m):
    return _save(store, P.polish_draft(doc, m.group(1), actor))

def r_draft_docx(ev, store, doc, actor, m):
    d = P.find_draft(doc, m.group(1))
    return _file(draft_docx(d, doc["inputs"]["society"]),
                 "application/vnd.openxmlformats-officedocument.wordprocessingml.document", draft_filename(d))

ROUTES = [
    ("GET", r"", r_get, "read"), ("DELETE", r"", r_delete, "secretary"), ("GET", r"/export", r_export, "read"),
    ("PUT", r"/society", r_society, "edit"), ("PUT", r"/bills", r_bills, "edit"), ("PUT", r"/quotes", r_quotes, "edit"),
    ("PUT", r"/flats", r_flats, "edit"), ("PUT", r"/assumptions", r_assumptions, "edit"), ("PUT", r"/events", r_events, "edit"),
    ("PUT", r"/members", r_members, "secretary"),
    ("POST", r"/documents", r_upload, "edit"), ("GET", r"/documents/(\w+)", r_doc_get, "read"),
    ("DELETE", r"/documents/(\w+)", r_doc_delete, "edit"),
    ("POST", r"/advance", r_advance, "edit"), ("POST", r"/clock/reset", r_clock_reset, "edit"),
    ("POST", r"/discom-reply", r_reply, "edit"), ("DELETE", r"/discom-reply", r_reply_clear, "edit"),
    ("PUT", r"/drafts/(\w+)", r_draft_edit, "edit"), ("POST", r"/drafts/(\w+)/approve", r_draft_approve, "edit"),
    ("GET", r"/drafts/(\w+)/docx", r_draft_docx, "read"),
    ("POST", r"/review", r_review, "edit"), ("POST", r"/drafts/(\w+)/polish", r_draft_polish, "edit"),
]

def _route(event: dict, method: str, path: str):
    if method == "OPTIONS":
        return _resp(204, {}), None
    if method == "GET" and path == "/health":
        return _resp(200, {"ok": True}), None
    if method == "GET" and path == "/rules":
        return _resp(200, {"rules": rules.list_rules(), "states": rules.INDIA_STATES}), None
    store = get_store()
    if method == "POST" and path == "/projects":
        b = _parse(event, S.CreateProject)
        doc, key = P.create(new_id(), b)
        doc["alarm_at"] = alarm.sync(doc)
        store.put(doc["id"], doc)
        return _resp(201, {**P.public(doc), "access_key": key}), doc["id"]
    pm = re.fullmatch(r"/projects/([0-9a-f]{10})(/.*)?", path)
    if not pm:
        raise P.ProjectError(404, "not found")
    pid, sub = pm.group(1), pm.group(2) or ""
    for meth, pattern, fn, who in ROUTES:
        m = re.fullmatch(pattern, sub)
        if meth == method and m:
            doc = store.get(pid)
            if not doc:
                raise P.ProjectError(404, "unknown or expired project")
            P.check_key(doc, _header(event, "x-project-key"))
            actor = _header(event, "x-actor")
            if who == "edit":
                actor = P.require_role(doc, actor)["name"]
            elif who == "secretary":
                actor = P.require_role(doc, actor, ("secretary",))["name"]
            return fn(event, store, doc, actor, m), pid
    raise P.ProjectError(404, "not found")

def handler(event, context=None):
    started, rid = time.time(), uuid.uuid4().hex[:12]
    method = event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod", "GET")
    path = event.get("rawPath") or event.get("path", "/")
    pid = None
    try:
        resp, pid = _route(event, method, path)
    except P.ProjectError as e:
        resp = _resp(e.status, {"error": e.message, "request_id": rid})
    except Exception:
        log.exception(json.dumps({"event": "unhandled_error", "request_id": rid, "method": method}))
        resp = _resp(500, {"error": "something went wrong on our side", "request_id": rid})
    log.info(json.dumps({"request_id": rid, "method": method, "route": re.sub(r"/[0-9a-f]{8,10}", "/:id", path),
                         "status": resp["statusCode"], "ms": round((time.time() - started) * 1000), "project": pid}))
    return resp
