import json
from solarsabha.handlers.api import handler

def _ev(method, path, body=None, key=None, actor=None):
    headers = {k: v for k, v in {"x-project-key": key, "x-actor": actor}.items() if v}
    return {"requestContext": {"http": {"method": method}}, "rawPath": path, "headers": headers,
            "body": json.dumps(body) if body is not None else None}

def test_api_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCAL_STATE_DIR", str(tmp_path))
    r = handler(_ev("POST", "/projects", {"sample": True})); assert r["statusCode"] == 201
    doc = json.loads(r["body"]); pid, key = doc["id"], doc["access_key"]
    who = dict(key=key, actor="Meera (sample)")
    r = handler(_ev("POST", f"/projects/{pid}/advance", {"days": 45}, **who)); d = json.loads(r["body"])
    assert d["result"]["next_action"]["status"] == "OVERDUE"
    r = handler(_ev("POST", f"/projects/{pid}/discom-reply", {"text": "Sanctioned load is insufficient. Maximum permissible solar is 25 kW."}, **who))
    assert json.loads(r["body"])["result"]["plan_v2"]["plan"]["recommended_kw"] == 25
    did = json.loads(r["body"])["drafts"][0]["id"]
    r = handler(_ev("POST", f"/projects/{pid}/drafts/{did}/approve", {"name": "Arjun (sample)"}, **who))
    d = json.loads(r["body"])["drafts"][0]
    assert d["status"] == "APPROVED" and d["approved_by"] == "Arjun (sample)"

def test_agents_construct_without_calling_a_model(monkeypatch):
    monkeypatch.setenv("BEDROCK_MODEL_ID", "test-model-id"); monkeypatch.setenv("AWS_REGION", "ap-south-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "x"); monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "x")
    from solarsabha.agents import factory
    from solarsabha.trace import Trace
    sec = factory.build_secretary(Trace())
    assert {"reader", "auditor", "chaser"} <= set(sec.tool_names)

def test_trace_handler_records_tool_use_once():
    from solarsabha.trace import Trace, TraceHandler
    t = Trace(); h = TraceHandler(t, "Auditor")
    for _ in range(3): h(current_tool_use={"name": "audit_quote", "toolUseId": "1", "input": {"x": 1}})
    assert len(t.events) == 1 and t.events[0]["tool"] == "audit_quote"
