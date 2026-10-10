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
    monkeypatch.setenv("MODEL_PROVIDER", "bedrock"); monkeypatch.setenv("BEDROCK_MODEL_ID", "test-model-id"); monkeypatch.setenv("AWS_REGION", "ap-south-1")
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
    monkeypatch.setenv("MODEL_PROVIDER", "bedrock"); monkeypatch.setenv("BEDROCK_MODEL_ID", "test-model-id"); monkeypatch.setenv("AWS_REGION", "ap-south-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "x"); monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "x")
    from solarsabha.agents import factory
    from solarsabha.trace import Trace
    chaser = factory.build_chaser(Trace())
    assert "draft_discom_escalation" in chaser.tool_names and not any("send" in n for n in chaser.tool_names)

def test_mcp_tools_replace_builtins_without_name_clashes(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "bedrock"); monkeypatch.setenv("BEDROCK_MODEL_ID", "test-model-id"); monkeypatch.setenv("AWS_REGION", "ap-south-1")
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

def test_gemini_is_the_default_provider_and_builds_agents(monkeypatch):
    monkeypatch.delenv("MODEL_PROVIDER", raising=False); monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    from solarsabha.agents import factory
    from solarsabha.trace import Trace
    from strands.models.gemini import GeminiModel
    assert factory.provider() == "gemini" and isinstance(factory.model(), GeminiModel)
    assert factory.model().config["model_id"] == factory.DEFAULT_GEMINI_MODEL
    assert {"reader", "auditor", "chaser"} <= set(factory.build_secretary(Trace()).tool_names)

def test_gemini_key_comes_from_ssm_on_aws(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False); monkeypatch.setenv("GEMINI_KEY_PARAM", "/solarsabha/gemini-api-key")
    from solarsabha.agents import factory
    factory._ssm_secret.cache_clear()
    monkeypatch.setattr(factory, "_ssm_secret", lambda name: "from-ssm" if name == "/solarsabha/gemini-api-key" else None)
    assert factory.gemini_key() == "from-ssm" and factory.configured()

def test_quota_errors_fall_back_to_the_next_gemini_model(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "gemini"); monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL_ID", "model-a,model-b")
    import pytest
    from solarsabha.agents import factory
    factory._exhausted.clear()
    class ModelThrottledException(Exception):
        pass
    used = []
    def call():
        mid = factory.model().config["model_id"]; used.append(mid)
        if mid == "model-a":
            raise ModelThrottledException("429 RESOURCE_EXHAUSTED quotaId: GenerateRequestsPerDayPerProjectPerModel-FreeTier")
        return "answer from " + mid
    assert factory.run_with_fallback(call) == "answer from model-b" and used == ["model-a", "model-b"]
    assert factory.run_with_fallback(call) == "answer from model-b" and used[-1] == "model-b"   # model-a skipped now
    factory._exhausted.add("model-b")
    with pytest.raises(RuntimeError, match="daily free quota"):
        factory.run_with_fallback(call)
    factory._exhausted.clear()

def test_per_minute_limits_wait_and_retry_without_writing_the_model_off(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "gemini"); monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL_ID", "model-a,model-b")
    from solarsabha.agents import factory
    factory._exhausted.clear()
    slept = []
    monkeypatch.setattr(factory.time, "sleep", lambda s: slept.append(s))
    calls = []
    def call():
        calls.append(factory.model().config["model_id"])
        if len(calls) == 1:
            raise RuntimeError("429 RESOURCE_EXHAUSTED GenerateRequestsPerMinutePerProjectPerModel. Please retry in 7.5s.")
        return "ok"
    assert factory.run_with_fallback(call) == "ok"
    assert calls == ["model-a", "model-a"] and slept == [7.5] and "model-a" not in factory._exhausted   # no budget: wait as Google says

def test_daily_quota_is_read_from_the_underlying_google_error():
    from solarsabha.agents import factory
    class ClientError(Exception):
        pass
    class ModelThrottledException(Exception):
        pass
    try:
        try:
            raise ClientError("429 RESOURCE_EXHAUSTED {'quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier'}")
        except ClientError as inner:
            raise ModelThrottledException("You exceeded your current quota") from inner
    except ModelThrottledException as outer:
        assert factory._failure_kind(outer) == ("daily", 0)

def test_secretary_calls_specialists_one_at_a_time(monkeypatch):
    # a specialist agent cannot serve two calls at once ("agent is already processing a request")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    from strands.tools.executors import SequentialToolExecutor
    from solarsabha.agents import factory
    from solarsabha.trace import Trace
    assert isinstance(factory.build_secretary(Trace()).tool_executor, SequentialToolExecutor)

def test_backup_joins_the_chain_for_text_agents_only(monkeypatch):
    import pytest
    from solarsabha.agents import factory
    from strands.models.openai import OpenAIModel
    monkeypatch.delenv("MODEL_PROVIDER", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "g"); monkeypatch.setenv("GEMINI_MODEL_ID", "gem-a")
    monkeypatch.setenv("GROQ_API_KEY", "ignored")                     # not a supported provider
    monkeypatch.setenv("BAZAARLINK_API_KEY", "b"); monkeypatch.setenv("BAZAARLINK_MODEL_ID", "qwen/qwen3.7-flash:free")
    assert factory.backup_models() == ["bazaarlink:qwen/qwen3.7-flash:free"]
    monkeypatch.setattr(factory, "_exhausted", set())
    daily = RuntimeError("429 RESOURCE_EXHAUSTED GenerateRequestsPerDayPerProjectPerModel-FreeTier")
    seen = []
    def call():
        seen.append(factory.active_model())
        if factory.active_model() == "gem-a":
            raise daily
        m = factory.model()
        assert isinstance(m, OpenAIModel) and m.config["model_id"] == "qwen/qwen3.7-flash:free"
        assert m.client_args["base_url"] == "https://api.bazaarlink.ai/v1"
        return "ok"
    assert factory.run_with_fallback(call) == "ok" and seen == ["gem-a", "bazaarlink:qwen/qwen3.7-flash:free"]
    seen.clear(); factory._exhausted.clear()
    with pytest.raises(RuntimeError, match="daily free quota"):
        factory.run_with_fallback(call, documents=True)               # backups never get PDFs or photos
    assert seen == ["gem-a"]

def test_openai_style_rate_limit_messages_are_classified():
    from solarsabha.agents import factory
    tpd = RuntimeError("Error code: 429 - Rate limit reached for model `qwen/qwen3.7-flash` on tokens per day (TPD): "
                       "Limit 200000, Used 199500. Please try again in 7m12.5s.")
    tpm = RuntimeError("Error code: 429 - Rate limit reached on tokens per minute (TPM): Please try again in 2.5s.")
    assert factory._failure_kind(tpd) == ("daily", 0)
    assert factory._failure_kind(tpm) == ("minute", 2.5)

def test_garbled_tool_call_moves_to_the_next_model():
    from solarsabha.agents import factory as f
    assert f._failure_kind(RuntimeError("Parsing failed. The model generated output that could not be parsed. See 'failed_generation'"))[0] == "busy"
    from solarsabha.agents import factory
    e = RuntimeError("Tool call validation failed: attempted to call tool 'auditor<|channel|>commentary' which was not in request.tools")
    assert factory._failure_kind(e) == ("busy", 0)

def test_specialist_out_of_quota_stops_the_secretary(monkeypatch):
    # inside a specialist, a quota error must reach run_with_fallback instead of becoming a tool error the
    # Secretary keeps retrying on the same exhausted model
    from solarsabha.agents import factory
    daily = RuntimeError("429 RESOURCE_EXHAUSTED GenerateRequestsPerDayPerProjectPerModel-FreeTier")
    class Ctx:
        class agent:
            cancelled = False
            @classmethod
            def cancel(cls): cls.cancelled = True
    def build():
        def run(prompt): raise daily
        return run
    specialist = factory._specialist("auditor", "test", build)
    assert "out of quota" in specialist._tool_func(input="check quotes", tool_context=Ctx)
    assert Ctx.agent.cancelled and Ctx.agent.specialist_failure is daily
    class Sec:
        specialist_failure = daily
        def __call__(self, prompt, **kw): return "cancelled"
    import pytest
    with pytest.raises(RuntimeError, match="PerDay"):
        factory.ask(Sec(), "review")

def test_guardrail_lets_the_agent_return_its_structured_answer():
    # Strands returns structured output through a tool named after the answer model; blocking it made OpenAI-style
    # models loop and fail
    from types import SimpleNamespace
    from pydantic import BaseModel
    from strands.tools.structured_output.structured_output_tool import StructuredOutputTool
    from solarsabha.trace import Trace, TraceHooks
    class Answer(BaseModel):
        body: str
    trace = Trace(); hooks = TraceHooks(trace, "Secretary", allowed=set())
    answer = SimpleNamespace(tool_use={"name": "Answer", "input": {}}, selected_tool=StructuredOutputTool(Answer), cancel_tool=False)
    hooks.before_tool(answer); hooks.after_tool(answer)
    assert answer.cancel_tool is False and trace.events == []
    other = SimpleNamespace(tool_use={"name": "send_email", "input": {}}, selected_tool=None, cancel_tool=False)
    hooks.before_tool(other)
    assert "not allowed" in other.cancel_tool
