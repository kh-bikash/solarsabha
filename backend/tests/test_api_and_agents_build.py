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

def test_trace_hooks_record_real_outputs_and_block_other_tools():
    from types import SimpleNamespace as NS
    from solarsabha.trace import Trace, TraceHooks
    t = Trace(); h = TraceHooks(t, "Auditor", allowed={"audit_quote"})
    ok = NS(tool_use={"name": "audit_quote", "toolUseId": "1", "input": {"q": 1}}, cancel_tool=False)
    h.before_tool(ok); assert ok.cancel_tool is False
    h.after_tool(NS(tool_use=ok.tool_use, result={"status": "success", "content": [{"json": {"verdict": "RED"}}]}))
    assert t.events[-1]["tool"] == "audit_quote" and "RED" in t.events[-1]["output"]
    bad = NS(tool_use={"name": "send_email", "toolUseId": "2", "input": {}}, cancel_tool=False)
    h.before_tool(bad)
    assert bad.cancel_tool and "not allowed" in bad.cancel_tool and "Blocked" in t.events[-1]["output"]

def test_agents_only_get_their_own_tools(monkeypatch):
    monkeypatch.setenv("BEDROCK_MODEL_ID", "test-model-id"); monkeypatch.setenv("AWS_REGION", "ap-south-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "x"); monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "x")
    from solarsabha.agents import factory
    from solarsabha.trace import Trace
    chaser = factory.build_chaser(Trace())
    assert "draft_discom_escalation" in chaser.tool_names and not any("send" in n for n in chaser.tool_names)

def test_mcp_tools_replace_builtins_without_name_clashes(monkeypatch):
    monkeypatch.setenv("BEDROCK_MODEL_ID", "test-model-id"); monkeypatch.setenv("AWS_REGION", "ap-south-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "x"); monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "x")
    from strands import tool
    from solarsabha.agents import factory
    from solarsabha.trace import Trace
    @tool
    def get_rule(key: str) -> dict:
        """MCP version of get_rule."""
        return {}
    @tool
    def scan_for_injection(text: str) -> list:
        """MCP version of the injection scan."""
        return []
    sec = factory.build_secretary(Trace(), extra_tools=[get_rule, scan_for_injection])     # used to raise: duplicate name
    assert sec.tool_names.count("get_rule") == 1 and "scan_for_injection" not in sec.tool_names
    aud = factory.build_auditor(Trace(), extra_tools=[get_rule, scan_for_injection])
    assert "scan_for_injection" in aud.tool_names and aud.tool_names.count("get_rule") == 1
