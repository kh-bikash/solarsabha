"""Production behaviour of the API: access, roles, validation, uploads, edits, approvals, privacy."""
import base64
import json
from pathlib import Path

import pytest
from solarsabha.handlers.api import handler

PDFS = Path(__file__).resolve().parents[1] / "samples" / "pdfs"

def call(method, path, body=None, key=None, actor=None):
    headers = {k: v for k, v in {"x-project-key": key, "x-actor": actor}.items() if v}
    r = handler({"requestContext": {"http": {"method": method}}, "rawPath": path, "headers": headers,
                 "body": json.dumps(body) if body is not None else None})
    return r["statusCode"], (json.loads(r["body"]) if not r.get("isBase64Encoded") else r)

@pytest.fixture
def real(tmp_path, monkeypatch):
    """A new, empty, real project owned by its secretary."""
    monkeypatch.setenv("LOCAL_STATE_DIR", str(tmp_path))
    code, d = call("POST", "/projects", {"society": {"name": "Green Park CHS", "flats": 40, "city": "Pune", "state": "Maharashtra"},
                                         "you": {"name": "Asha", "role": "secretary"}, "consent": True})
    assert code == 201
    return d["id"], d["access_key"]

def test_new_project_needs_consent_and_details(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCAL_STATE_DIR", str(tmp_path))
    assert call("POST", "/projects", {"society": {"name": "X CHS", "flats": 10}, "you": {"name": "Asha"}})[0] == 400
    assert call("POST", "/projects", {})[0] == 400
    assert call("POST", "/projects", {"sample": True, "surprise": 1})[0] == 400       # unknown fields rejected

def test_special_category_state_gets_the_higher_subsidy(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCAL_STATE_DIR", str(tmp_path))
    body = lambda state: {"society": {"name": "Hill View CHS", "flats": 40, "state": state}, "you": {"name": "Asha"}, "consent": True}
    bills = {"bills": [{"month": f"2026-{m:02d}", "units_kwh": 4000} for m in range(1, 13)]}
    subsidy = {}
    for state in ("Assam", "Maharashtra"):
        _, d = call("POST", "/projects", body(state))
        _, d = call("PUT", f"/projects/{d['id']}/bills", bills, key=d["access_key"], actor="Asha")
        rec = d["result"]["recommended"]
        subsidy[state] = rec["subsidy"] / rec["kw"]
        assert d["result"]["rule_coverage"]["overrides"] == (1 if state == "Assam" else 0)
    assert subsidy == {"Assam": 19800, "Maharashtra": 18000}

def test_empty_project_waits_for_inputs(real):
    pid, key = real
    code, d = call("GET", f"/projects/{pid}", key=key)
    r = d["result"]
    assert code == 200 and r["plan"] is None and set(r["needs"]) >= {"bills", "quotes"}
    assert "key_hash" not in d and "access_key" not in d
    assert r["rule_coverage"]["state"] == "Maharashtra"

def test_key_and_roles_are_enforced(real):
    pid, key = real
    assert call("GET", f"/projects/{pid}")[0] == 401
    assert call("GET", f"/projects/{pid}", key="wrong")[0] == 401
    assert call("PUT", f"/projects/{pid}/assumptions", {"tariff": 8}, key=key)[0] == 403          # nobody chosen
    assert call("PUT", f"/projects/{pid}/assumptions", {"tariff": 8}, key=key, actor="Stranger")[0] == 403
    code, _ = call("PUT", f"/projects/{pid}/members", {"members": [{"name": "Asha", "role": "secretary"},
                                                                  {"name": "Ravi", "role": "viewer"}]}, key=key, actor="Asha")
    assert code == 200
    assert call("PUT", f"/projects/{pid}/assumptions", {"tariff": 8}, key=key, actor="Ravi")[0] == 403   # viewer
    assert call("PUT", f"/projects/{pid}/members", {"members": [{"name": "Ravi", "role": "member"}]}, key=key, actor="Asha")[0] == 400

def test_bills_assumptions_and_validation(real):
    pid, key = real
    bad = {"bills": [{"month": "2026-13", "units_kwh": 100}]}
    assert call("PUT", f"/projects/{pid}/bills", bad, key=key, actor="Asha")[0] == 400
    bills = {"bills": [{"month": f"2026-{m:02d}", "units_kwh": 4000, "amount_inr": 30000} for m in range(1, 7)]}
    code, d = call("PUT", f"/projects/{pid}/bills", bills, key=key, actor="Asha")
    r = d["result"]
    assert code == 200 and r["annual_kwh"] == 48000 and "more_bills" in r["needs"]
    assert r["bill_average_rate"] == 7.5
    kw_before = r["recommended"]["kw"]
    code, d = call("PUT", f"/projects/{pid}/assumptions", {"share": 0.5, "tariff": 9}, key=key, actor="Asha")
    a = d["result"]["assumptions"]
    assert a["share"]["source"] == "committee" and a["tariff"]["value"] == 9 and a["cost_per_kw"]["source"] == "rulebook"
    assert d["result"]["recommended"]["kw"] < kw_before

def test_upload_reads_bill_and_quote_pdfs(real):
    pid, key = real
    for f, kind in [("bill_2025-10.pdf", "bill"), ("quote_sasta.pdf", "quote")]:
        body = {"kind": kind, "filename": f, "content_base64": base64.b64encode((PDFS / f).read_bytes()).decode()}
        code, d = call("POST", f"/projects/{pid}/documents", body, key=key, actor="Asha")
        assert code == 200, d
    docs = d["documents"]
    assert [x["status"] for x in docs] == ["READ", "READ"]
    assert d["inputs"]["bills"][0]["month"] == "2025-10" and d["inputs"]["bills"][0]["source_doc"] == docs[0]["id"]
    audit = d["result"]["audits"][0]
    assert audit["verdict"] == "RED" and any(f["code"] == "DOCUMENT_CONTAINS_INSTRUCTIONS" for f in audit["flags"])
    code, f = call("GET", f"/projects/{pid}/documents/{docs[0]['id']}", key=key)
    assert code == 200 and base64.b64decode(f["body"]).startswith(b"%PDF")
    code, d = call("DELETE", f"/projects/{pid}/documents/{docs[0]['id']}", key=key, actor="Asha")
    assert code == 200 and len(d["documents"]) == 1 and d["inputs"]["bills"][0]["source_doc"] is None

def test_upload_rejects_non_documents(real):
    pid, key = real
    body = {"kind": "bill", "filename": "x.exe", "content_base64": base64.b64encode(b"MZ-not-a-pdf").decode()}
    assert call("POST", f"/projects/{pid}/documents", body, key=key, actor="Asha")[0] == 400

def test_draft_edit_approval_and_docx(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCAL_STATE_DIR", str(tmp_path))
    _, d = call("POST", "/projects", {"sample": True})
    pid, key = d["id"], d["access_key"]
    who = dict(key=key, actor="Meera (sample)")
    did = d["drafts"][0]["id"]
    code, d = call("POST", f"/projects/{pid}/drafts/{did}/approve", {"name": "Treasurer (sample)"}, **who)
    assert code == 403                                                    # viewers cannot approve
    code, d = call("POST", f"/projects/{pid}/drafts/{did}/approve", {"name": "Meera (sample)"}, **who)
    assert d["drafts"][0]["status"] == "APPROVED"
    code, d = call("PUT", f"/projects/{pid}/drafts/{did}", {"subject": "Notice: AGM", "body": "New text", "editor": "Arjun (sample)"}, **who)
    dr = d["drafts"][0]
    assert dr["status"] == "DRAFT" and dr["stale_approval"]["by"] == "Meera (sample)" and dr["body"] == "New text"
    code, f = call("GET", f"/projects/{pid}/drafts/{did}/docx", key=key)
    assert code == 200 and base64.b64decode(f["body"])[:2] == b"PK"      # a .docx is a zip
    assert d["drafts"][0]["id"] == did                                    # ids are stable across recomputes

def test_events_by_date_and_clock(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCAL_STATE_DIR", str(tmp_path))
    _, d = call("POST", "/projects", {"sample": True})
    pid, key = d["id"], d["access_key"]
    who = dict(key=key, actor="Meera (sample)")
    assert d["result"]["clock"]["today_day"] == 10 and d["result"]["next_action"]["stage"] == "FEASIBILITY"
    assert call("PUT", f"/projects/{pid}/events", {"events": [{"stage": "AGM", "done_on": "2099-01-01"}]}, **who)[0] == 400
    code, d = call("POST", f"/projects/{pid}/advance", {"days": 40}, **who)
    assert d["result"]["clock"] == {**d["result"]["clock"], "today_day": 50, "simulated": True}
    code, d = call("POST", f"/projects/{pid}/clock/reset", {}, **who)
    assert d["result"]["clock"]["today_day"] == 10 and not d["result"]["clock"]["simulated"]

def test_export_and_delete(real):
    pid, key = real
    code, d = call("GET", f"/projects/{pid}/export", key=key)
    assert code == 200 and "key_hash" not in d and d["consent"]["accepted"] and d["audit"]
    assert call("DELETE", f"/projects/{pid}", {"confirm_name": "wrong"}, key=key, actor="Asha")[0] == 400
    assert call("DELETE", f"/projects/{pid}", {"confirm_name": "green park chs"}, key=key, actor="Asha")[0] == 200
    assert call("GET", f"/projects/{pid}", key=key)[0] == 404

def test_expired_projects_disappear(real, tmp_path):
    pid, key = real
    path = tmp_path / f"{pid}.json"
    doc = json.loads(path.read_text()); doc["expires_at"] = 1; path.write_text(json.dumps(doc))
    assert call("GET", f"/projects/{pid}", key=key)[0] == 404

def test_scheduled_wake_rechecks_and_logs(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCAL_STATE_DIR", str(tmp_path))
    from solarsabha.handlers.wake import handler as wake
    _, d = call("POST", "/projects", {"sample": True})
    path = tmp_path / f"{d['id']}.json"
    doc = json.loads(path.read_text()); doc["sim_offset_days"] = 40; path.write_text(json.dumps(doc))
    r = wake({"project_id": d["id"]})
    assert r["ok"] and r["next_action"]["status"] == "OVERDUE"
    assert json.loads(path.read_text())["audit"][-1]["actor"] == "Chaser (scheduled)"
    assert wake({"project_id": "0000000000"}) == {"ok": False, "reason": "unknown or expired project"}

def test_unknown_routes_and_bad_json(real):
    pid, key = real
    assert call("GET", "/nope")[0] == 404
    r = handler({"requestContext": {"http": {"method": "PUT"}}, "rawPath": f"/projects/{pid}/bills",
                 "headers": {"x-project-key": key, "x-actor": "Asha"}, "body": "{not json"})
    assert r["statusCode"] == 400
