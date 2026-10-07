"""One Lambda behind API Gateway (HTTP API, payload v2). Also used by scripts/dev_server.py for local dev.

Routes
  POST /projects                      create a demo project (offline pipeline on bundled sample data)
  GET  /projects/{id}                 current state
  POST /projects/{id}/advance         body {"days": N}   move the SIMULATED clock; Chaser logic re-runs
  POST /projects/{id}/discom-reply    body {"text": "..."}  simulated inbound DISCOM email -> replan
  POST /projects/{id}/drafts/{did}/approve   mark a draft APPROVED (nothing is sent in this build)
  GET  /rules                         the rulebook
"""
import json, re
from .. import rules
from ..pipeline import run_offline, load_sample_inputs
from ..state import get_store, new_id

def _resp(code, body):
    return {"statusCode": code, "headers": {"content-type": "application/json", "access-control-allow-origin": "*"}, "body": json.dumps(body, default=str)}

def _recompute(doc):
    inputs = load_sample_inputs()
    out = run_offline(inputs, today_day=doc["today_day"], events=doc["events"], discom_reply=doc.get("discom_reply"))
    approved = {d["kind"] + d["to"] for d in doc.get("drafts", []) if d["status"] == "APPROVED"}
    for d in out["drafts"]:
        if d["kind"] + d["to"] in approved:
            d["status"] = "APPROVED"
    doc.update({"today_day": doc["today_day"], "result": out, "drafts": out["drafts"]})
    return doc

def handler(event, context=None):
    method = event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod", "GET")
    path = event.get("rawPath") or event.get("path", "/")
    body = json.loads(event["body"]) if event.get("body") else {}
    store = get_store()
    if method == "OPTIONS":
        return _resp(200, {})
    if method == "GET" and path == "/rules":
        return _resp(200, rules.list_rules())
    if method == "POST" and path == "/projects":
        pid = new_id()
        doc = _recompute({"id": pid, "today_day": 0, "events": load_sample_inputs()["events"], "drafts": []})
        store.put(pid, doc); return _resp(201, doc)
    m = re.fullmatch(r"/projects/([\w-]+)(/.*)?", path)
    if not m:
        return _resp(404, {"error": "not found"})
    pid, sub = m.group(1), m.group(2) or ""
    doc = store.get(pid)
    if not doc:
        return _resp(404, {"error": "unknown project"})
    if method == "GET" and sub == "":
        return _resp(200, doc)
    if method == "POST" and sub == "/advance":
        doc["today_day"] += int(body.get("days", 1)); doc = _recompute(doc); store.put(pid, doc); return _resp(200, doc)
    if method == "POST" and sub == "/discom-reply":
        doc["discom_reply"] = body.get("text", ""); doc = _recompute(doc); store.put(pid, doc); return _resp(200, doc)
    a = re.fullmatch(r"/drafts/(\w+)/approve", sub)
    if method == "POST" and a:
        for d in doc["drafts"]:
            if d["id"] == a.group(1):
                d["status"] = "APPROVED"
        doc["result"]["drafts"] = doc["drafts"]; store.put(pid, doc); return _resp(200, doc)
    return _resp(404, {"error": "not found"})
