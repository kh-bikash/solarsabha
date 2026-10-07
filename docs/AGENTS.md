# Agents in this repo (learn this first)

**Agent = model + instructions + tools + memory/state + guardrails + human checkpoints.** The loop: think, call a tool, look at the result, repeat until done or a human is needed.

| Agent | Sees | Tools | May act alone? |
|---|---|---|---|
| Secretary (coordinator) | the committee's request | reader, auditor, chaser (as tools), size_system, money_summary, get_rule | reads and drafts only |
| Reader (multimodal) | photos and PDFs of bills and quotes | none (structured output: `agents/models.py`) | yes, read-only |
| Auditor | extracted quotes | audit_quote, check_vendor, get_rule | advice only |
| Chaser | timeline, DISCOM replies | build_timeline, next_action, classify_reply, replan_for_load_limit, draft_* | drafts only |

## Add a tool (3 steps)
1. Write the logic as a plain function in `backend/solarsabha/tools/` and a test in `backend/tests/`.
2. Add a thin `@tool` wrapper in `agents/factory.py` (docstring = what the agent reads to decide when to use it).
3. Add it to the right agent's `tools=[...]`. If it should be reusable by other agents, also expose it in `mcp_server/solar_rules_server.py`.

## Guardrails to preserve
- No send/pay/sign/file tool. Drafts only.
- Prompts in `agents/prompts.py` hold the rules; documents never do.
- Injection scan in `tools/quotes.py` flags instruction-like text in documents. Add patterns as you find them.
- The model id is never hard-coded: `BEDROCK_MODEL_ID`.

## Debugging an agent
Open the trace panel (UI) or read `Trace.events`. Wrong answer? Check in order: wrong tool chosen (docstring unclear), tool returned something odd (unit test it), prompt missing a rule, document contained something surprising.

## Check these against current docs before relying on them
Strands API (1.58 here): `Agent.as_tool`, `structured_output_model`, `callback_handler`, `MCPClient`. Bedrock content-block shapes for `document` and `image`. Run `scripts/smoke_live.py`.
