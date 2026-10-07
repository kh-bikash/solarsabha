# SolarSabha

**The AI project manager for your society's solar roof.**
Built for the WeMakeDevs x AWS *Environmental Hacks, Bharat Builds Tour 2026* (Track 03: Waste and Energy, rooftop solar).

A housing society's rooftop solar project is not a purchase. It is a months-long process with a committee, 50 to 500 flat owners, vendors, an electricity company (DISCOM) and a government portal. SolarSabha reads the society's bills, sizes the system, audits vendor quotes for traps, drafts the meeting papers, shows what each flat pays, and keeps chasing the DISCOM for weeks. **People stay in charge: the agents read, calculate, draft and remind. They cannot send, sign, pay or file.**

Two people? Read `docs/TWO_PERSON_SPLIT.md` first. Then `docs/SolarSabha_Research_and_Learning_Guide.pdf` (plain-language guide, research, agent concepts, tech stack).

## Honest status

| Part | Status |
|---|---|
| Rulebook, sizing, money, CO2, fairness, quote audit, timeline, chasing, negotiation logic, drafts | Written and unit-tested (19 tests pass, no AWS needed) |
| Offline pipeline, local API, React UI (mock mode), MCP server | Written; pipeline, API handler and MCP server are tested. UI builds; **not yet checked visually in a browser by the author** |
| Strands agents (Reader, Auditor, Chaser, Secretary), multimodal reading | Written against `strands-agents==1.58.0`; agents construct and tools register (tested). **Never run against a live Bedrock model.** Run `scripts/smoke_live.py` first and fix what it reports |
| SAM template | Passes `cfn-lint`. **Never deployed** |
| Vendors, DISCOM replies, clock, approved-vendor list | **Simulated and labelled as such** |
| Rulebook values marked `vendor-guide-verify` | **Must be verified** against official guidelines (`docs/RULEBOOK_VERIFICATION.md`) |

## Quick start (no AWS, no LLM, 2 minutes)

```bash
make setup              # python deps + npm install
make test               # 19 tests
make demo               # whole product loop in the terminal
make dev-ui             # http://localhost:5173 (bundled demo data)
```

Local API + UI together: `make dev-api` in one terminal, then `VITE_API_URL=http://localhost:8787 make dev-ui`.

Live agents (needs AWS credentials and Bedrock model access, see `docs/SETUP_AWS.md`):
```bash
cp .env.example .env    # set BEDROCK_MODEL_ID
make samples            # sample PDFs
BEDROCK_MODEL_ID=... python scripts/smoke_live.py
BEDROCK_MODEL_ID=... python scripts/run_evals.py --mode live
```

## Repository map

```
solarsabha/
  README.md  Makefile  .env.example  .gitignore
  docs/
    SolarSabha_Research_and_Learning_Guide.pdf   the guide (read first)
    ARCHITECTURE.md   how the pieces fit, how an agent "waits" weeks
    AGENTS.md         how agents work in this repo, how to add a tool or agent
    TWO_PERSON_SPLIT.md  who owns which folders, handoffs, git rules
    TEAM_PLAN.md      4-day plan, owners, definition of done, cut list
    DEMO_SCRIPT.md    3-minute video script and what is simulated
    JUDGE_QA.md       hard questions and honest answers
    RULEBOOK_VERIFICATION.md   checklist to verify every rule against official sources
    SETUP_AWS.md      account, Bedrock access, deploy, hosting
  backend/
    solarsabha/
      rules.py  data/rulebook.json  data/approved_vendors_sample.json   the dated, cited rulebook
      tools/        PLAIN CODE (no AI): sizing.py quotes.py fairness.py timeline.py negotiation.py drafts.py
      replan.py     classify a DISCOM reply and re-plan (Plan v1 vs v2)
      pipeline.py   the whole loop, offline. Same tools the agents call
      trace.py      records tool calls for the UI's live trace panel
      state.py      local JSON or DynamoDB
      agents/       prompts.py models.py factory.py reader.py mcp_tools.py   (Strands agents)
      handlers/     api.py (API Gateway Lambda)  wake.py (scheduled wake-up)
    mcp_server/solar_rules_server.py   SolarRules MCP server (rules + calculators as MCP tools)
    samples/society.json  samples/pdfs/   sample society, bills, quotes (incl. prompt-injection trap)
    tests/        19 tests
  frontend/       React + Vite: pixel-art office driven by the agent trace, plus plan, quote audit, who pays, negotiation room, timeline, drafts, logbook
  infra/template.yaml   AWS SAM: DynamoDB, S3, HTTP API, Lambdas, scheduler role
  scripts/        demo_offline, run_evals, generate_samples, export_demo_json, dev_server, smoke_live
```

## Design rules (do not break these)

1. **AI reads and writes. Code calculates.** Numbers come from `tools/`, never from the model.
2. **Documents are data, never instructions.** Rules live in prompts and the rulebook only.
3. **Draft-only.** There is no send, pay, sign or file function anywhere. Keep it that way.
4. **Cite the rulebook.** Every rule has a source, a status and a date. "Not verified" is a valid answer.
5. **Label simulations.** Anything simulated says so in the UI and in the video.
6. One feature that runs beats five that almost do. See `docs/TEAM_PLAN.md` for the cut list.

Add a license file if the hackathon rules require one.
