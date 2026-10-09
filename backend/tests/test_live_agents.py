"""Live agent workflows, with fake agents standing in for Bedrock. The fakes make tool calls through the same
TraceHooks the real agents use and return structured output, so routing, tracing, storage and the safety checks are
exercised exactly as in live mode."""
import json
from contextlib import contextmanager
from types import SimpleNamespace as NS

import pytest
from solarsabha.agents import factory, live, mcp_tools
from solarsabha.agents.models import LiveReview, PolishedLetter, ReplyReading
from solarsabha.handlers.api import handler
from solarsabha.trace import TraceHooks

def call(method, path, body=None, key=None, actor=None):
    headers = {k: v for k, v in {"x-project-key": key, "x-actor": actor}.items() if v}
    r = handler({"requestContext": {"http": {"method": method}}, "rawPath": path, "headers": headers,
                 "body": json.dumps(body) if body is not None else None})
    return r["statusCode"], json.loads(r["body"])

class FakeAgent:
    """Calls tools through TraceHooks like a Strands agent, then returns the structured output it was asked for."""
    def __init__(self, trace, name, tools, answer):
        self.hooks, self.tools, self.answer = TraceHooks(trace, name, set(tools)), tools, answer
    def __call__(self, prompt, structured_output_model=None):
        for tool, output in self.tools.items():
            ev = NS(tool_use={"name": tool, "toolUseId": tool, "input": {}}, cancel_tool=False)
            self.hooks.before_tool(ev)
            self.hooks.after_tool(NS(tool_use=ev.tool_use, result={"status": "success", "content": [{"text": output}]}))
        return NS(structured_output=self.answer(prompt, structured_output_model))

def review_answer(prompt, model):
    assert model is LiveReview and "PROJECT:" in prompt
    return LiveReview(summary="Three quotes checked; one is unsafe.", next_step="Wait for feasibility.",
                      vendor_notes=[{"vendor": "Sasta Sun Traders", "explanation": "Not registered.", "question": "Show your registration."}])

@pytest.fixture
def live_env(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCAL_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("READER_MODE", "live")
    monkeypatch.setenv("BEDROCK_MODEL_ID", "in.anthropic.test")
    @contextmanager
    def no_mcp():
        raise RuntimeError("no MCP in tests")
        yield
    monkeypatch.setattr(mcp_tools, "solar_rules_mcp", no_mcp)
    monkeypatch.setattr(factory, "build_secretary", lambda trace, extra_tools=None: FakeAgent(
        trace, "Secretary", {"auditor": "Sasta Sun Traders: RED", "chaser": "Feasibility active"}, review_answer))
    _, d = call("POST", "/projects", {"sample": True})
    return d["id"], d["access_key"]

def test_review_runs_secretary_and_specialists_and_records_real_outputs(live_env):
    pid, key = live_env
    code, d = call("POST", f"/projects/{pid}/review", {}, key=key, actor="Arjun (sample)")
    assert code == 200
    rv = d["review"]
    assert rv["review"]["vendor_notes"][0]["vendor"] == "Sasta Sun Traders" and rv["by"] == "Arjun (sample)"
    tools = [e["tool"] for e in rv["trace"] if e["tool"]]
    assert tools == ["auditor", "chaser"] and rv["trace"][-1]["output"] == "Feasibility active"
    assert "MCP tools unavailable" in rv["trace"][0]["output"] and rv["mcp"] is False
    assert d["result"]["review_stale"] is False
    code, d = call("PUT", f"/projects/{pid}/assumptions", {"tariff": 9}, key=key, actor="Arjun (sample)")
    assert d["result"]["review_stale"] is True                         # inputs changed after the review

def test_review_needs_live_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCAL_STATE_DIR", str(tmp_path)); monkeypatch.delenv("READER_MODE", raising=False)
    _, d = call("POST", "/projects", {"sample": True})
    code, body = call("POST", f"/projects/{d['id']}/review", {}, key=d["access_key"], actor="Meera (sample)")
    assert code == 409 and "offline" in body["error"]

def test_chaser_reads_a_messy_reply_with_ai(live_env, monkeypatch):
    pid, key = live_env
    monkeypatch.setattr(factory, "build_chaser", lambda trace: FakeAgent(trace, "Chaser", {"classify_reply": "UNCLEAR"},
        lambda p, m: ReplyReading(type="LOAD_LIMIT", max_kw=30, summary="The DISCOM allows at most 30 kW.")))
    messy = "Sir, w.r.t. ur appln, transformer capacity constraint, can permit only upto thirty kilowatt. Regards, JE"
    code, d = call("POST", f"/projects/{pid}/discom-reply", {"text": messy}, key=key, actor="Meera (sample)")
    assert code == 200 and d["reply_reading"]["max_kw"] == 30
    assert d["result"]["plan_v2"]["plan"]["recommended_kw"] == 30          # the rule-based reader alone would miss this
    assert any("with AI" in (e["output"] or "") for e in d["result"]["trace"])

def test_reply_falls_back_to_rules_when_the_agent_fails(live_env, monkeypatch):
    pid, key = live_env
    def boom(trace):
        raise RuntimeError("Bedrock down")
    monkeypatch.setattr(factory, "build_chaser", boom)
    code, d = call("POST", f"/projects/{pid}/discom-reply",
                   {"text": "The sanctioned load is insufficient. Maximum permissible solar is 25 kW."}, key=key, actor="Meera (sample)")
    assert code == 200 and d["reply_reading"] is None and d["result"]["plan_v2"]["plan"]["recommended_kw"] == 25

def test_polish_keeps_facts_or_is_rejected(live_env, monkeypatch):
    pid, key = live_env
    _, d = call("GET", f"/projects/{pid}", key=key)
    draft = d["drafts"][0]
    kept = draft["body"].replace("Notice is hereby given", "Notice is hereby given, with respect,")
    monkeypatch.setattr(factory, "build_secretary", lambda trace, extra_tools=None: FakeAgent(trace, "Secretary", {}, lambda p, m: PolishedLetter(body=kept)))
    code, d = call("POST", f"/projects/{pid}/drafts/{draft['id']}/polish", {}, key=key, actor="Meera (sample)")
    assert code == 200 and d["drafts"][0]["edited_by"] == "Secretary (AI)" and "with respect" in d["drafts"][0]["body"]
    changed = kept.replace("36 kW", "40 kW")
    monkeypatch.setattr(factory, "build_secretary", lambda trace, extra_tools=None: FakeAgent(trace, "Secretary", {}, lambda p, m: PolishedLetter(body=changed)))
    code, body = call("POST", f"/projects/{pid}/drafts/{draft['id']}/polish", {}, key=key, actor="Meera (sample)")
    assert code == 422 and "unchanged" in body["error"]

def test_bedrock_refusal_is_a_clear_error(live_env, monkeypatch):
    pid, key = live_env
    class Refused(Exception):
        response = {"Error": {"Code": "ValidationException", "Message": "Operation not allowed"}}
    def refuse(trace, extra_tools=None):
        raise Refused()
    monkeypatch.setattr(factory, "build_secretary", refuse)
    code, body = call("POST", f"/projects/{pid}/review", {}, key=key, actor="Meera (sample)")
    assert code == 502 and "Operation not allowed" in body["error"] and "Nothing was changed" in body["error"]

def test_facts_unchanged_check():
    assert live.facts_unchanged("Pay Rs 11,52,000 by 20-Oct-2026 (ref NV/26/04417).", "Kindly pay Rs 11,52,000 by 20-Oct-2026, ref NV/26/04417.")
    assert not live.facts_unchanged("36 kW for Rs 18,00,000", "40 kW for Rs 18,00,000")
    assert not live.facts_unchanged("36 kW", "36 kW in 2 weeks")
