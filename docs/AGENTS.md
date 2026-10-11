# Agents in this repo (learn this first)

**Agent = model + instructions + tools + memory/state + guardrails + human checkpoints.** The loop: think, call a tool, look at the result, repeat until done or a human is needed.

| Agent | Sees | Tools | May act alone? |
|---|---|---|---|
| Secretary (coordinator) | the project facts (as data) | reader, auditor, chaser (as tools, one at a time), size_system, money_summary, get_rule | reads and drafts only |
| Reader (multimodal) | photos and PDFs of bills and quotes | none (structured output: `agents/models.py`) | yes, read-only |
| Auditor | extracted quotes | audit_quote, check_vendor, scan_for_injection, get_rule | advice only |
| Chaser | timeline, DISCOM replies | build_timeline, next_action, classify_reply, replan_for_load_limit, draft_* | drafts only |

## Add a tool (3 steps)
1. Write the logic as a plain function in `backend/solarsabha/tools/` and a test in `backend/tests/`.
2. Add a thin `@tool` wrapper in `agents/factory.py` (docstring = what the agent reads to decide when to use it).
3. Add it to the right agent's `tools=[...]`. If it should be reusable by other agents, also expose it in `mcp_server/solar_rules_server.py`.

## How the pieces fit
- `agents/factory.py` builds every agent. Each specialist is exposed to the Secretary as a tool that builds a **fresh**
  agent per call (a shared agent refuses a second call while busy), and the Secretary runs them one at a time.
- Every agent returns a typed Pydantic answer (`agents/models.py`). Strands delivers it through an answer tool, which
  the guardrail always allows.
- Every model call goes through `run_with_fallback()`: a chain of Gemini models, then the optional BazaarLink backup for
  text, with time budgets (20 s inside a request). See the technical guide, section 8.

## Guardrails to preserve
- No send/pay/sign/file tool. Drafts only.
- Prompts in `agents/prompts.py` hold the rules; documents never do.
- Injection scan in `tools/quotes.py` flags instruction-like text in documents. Add patterns as you find them.
- The model is never hard-coded: `MODEL_PROVIDER` (gemini or bedrock), `GEMINI_MODEL_ID` (the chain), `BEDROCK_MODEL_ID`.
- `TraceHooks` (`trace.py`) cancels any tool outside an agent's allowlist. Add new tools to the agent's list, never bypass it.
- AI never does arithmetic: numbers come from `tools/`.

## Debugging an agent
Open the Logbook folder (UI) or read `Trace.events`. Wrong answer? Check in order: wrong tool chosen (docstring unclear), tool returned something odd (unit test it), prompt missing a rule, document contained something surprising.

## Testing without spending AI quota
Agent tests in `backend/tests/test_live_agents.py` replace the model with fakes that call the real tools, so wiring,
guardrails and fallbacks are tested offline. `scripts/smoke_live.py` makes one real model call; run it only when needed.

Strands API used (1.58): `@tool(context=True)`, `structured_output_model`, `SequentialToolExecutor`, `ModelRetryStrategy`,
hooks (`BeforeToolCallEvent`, `AfterToolCallEvent`), `MCPClient`, `GeminiModel`, `OpenAIModel`, `BedrockModel`.
