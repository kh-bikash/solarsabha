# Two-person split (share this with your teammate)

Swap A and B freely. Whoever is stronger on agents should take A.

## Person A: Agents and intelligence ("the brain")
Owns these folders and files (only A edits them without asking):
```
backend/solarsabha/agents/        prompts.py  models.py  factory.py  reader.py  mcp_tools.py
backend/solarsabha/tools/         sizing, quotes, fairness, timeline, negotiation, drafts
backend/solarsabha/replan.py  pipeline.py  trace.py  rules.py
backend/solarsabha/data/          rulebook.json  approved_vendors_sample.json
backend/mcp_server/               solar_rules_server.py
backend/samples/                  society.json  pdfs/
backend/tests/
scripts/                          run_evals.py  smoke_live.py  generate_samples.py  export_demo_json.py  demo_offline.py
docs/AGENTS.md  docs/RULEBOOK_VERIFICATION.md
```
Jobs, in order:
1. Get AWS credentials and Bedrock model access. Run `python scripts/smoke_live.py` and fix what breaks (`docs/SETUP_AWS.md`).
2. Make the Reader read the sample PDFs and photos correctly: `python scripts/run_evals.py --mode live`. Aim for a score you can show in the video.
3. Add a live path in `pipeline.py` (`run_live`) that uses the Reader's output but keeps ALL numbers from `tools/`.
4. Auditor explanations, Chaser reply handling, Secretary calling specialists; keep the live trace working.
5. Verify the rulebook against official sources (`docs/RULEBOOK_VERIFICATION.md`). Keep tests green.

## Person B: Platform and product surface ("the body")
Owns:
```
frontend/                         everything (App.jsx, components/, api.js, styles.css, mock/)
infra/template.yaml  infra/samconfig (local only)
backend/solarsabha/handlers/      api.py  wake.py
backend/solarsabha/state.py
backend/requirements*.txt  Makefile  README.md  .env.example
docs/ARCHITECTURE.md  docs/SETUP_AWS.md  docs/DEMO_SCRIPT.md  docs/JUDGE_QA.md  docs/TEAM_PLAN.md
```
Jobs, in order:
1. Run `make setup && make dev-ui`. Check every screen in a real browser (the UI has never been visually tested) and fix layout and the arena animation.
2. Deploy: `cd infra && sam build && sam deploy --guided`. Host the UI (Amplify). Share the API URL with A.
3. Add file upload (S3 pre-signed URL) and a screen to upload bills and quotes.
4. Scheduler: create one-time EventBridge schedules that invoke `WakeFunction`; keep the "time machine" button as the demo fallback.
5. Own the story: one real interview with a society secretary, the video (`docs/DEMO_SCRIPT.md`), README, blog, submission.

## The contract between you (do not break it)
The UI reads one JSON object, produced by `run_offline()` today and by the live path later. Its shape is the contract: see `frontend/src/mock/demo.json`.
Keys: `society, annual_kwh, plan, money, recommended, plan_v2, audits, negotiations, fairness, timeline, next_action, drafts, trace, today_day, simulated_parts`.
- A may ADD keys freely. A must tell B before renaming or removing one.
- B must not compute numbers in the UI. Show what the backend returns.
- After any change to the pipeline, A runs `make export-demo` and commits `demo.json`.

## Git rules (simple)
- Branches: `a/<topic>`, `b/<topic>`. Merge to `main` at least twice a day, after `make test` passes.
- Shared files (`README.md`, `Makefile`): B edits; A asks.
- Never commit `.env`, `.state/`, `node_modules/`, `.aws-sam/`.

## Handoff points
| When | A delivers | B delivers |
|---|---|---|
| End of Thu 8 Oct | `smoke_live` passes; Reader eval score | deployed API URL; UI online; UI checked in a browser |
| End of Fri 9 Oct | live path returns the contract shape; trace events stream | upload screen; UI shows live data |
| Sat 10 Oct (together) | Chaser + reply + Plan v2 live | scheduler wake + time machine + arena polish |
| Sun 11 Oct | bug fixes until noon | video, README, blog, submit 3+ hours early |

## If you fall behind
Cut from the bottom: local-language audio, extra connectors, 3D, terrace photo scout. Never cut: Reader on real PDFs, quote audit, the time-jump loop, labelling of simulated parts.
