# Team plan (4 days, 8 to 11 Oct 2026)

The event page says project work starts when the clock does. Before 8 Oct: learn (Strands quickstart, Step Functions callbacks, Bedrock console), set up accounts, read the guide. Ask on Discord whether preparing sample documents beforehand is allowed.

## Roles (adapt to team size; with 2 people merge A+D and B+C)
| Role | Owns |
|---|---|
| A Frontend | `frontend/`: wire LIVE mode, polish arena (2D/2.5D only), trace panel, video capture |
| B Backend/AWS | `infra/`, deploy, DynamoDB, scheduler wake, S3 upload, API |
| C Agents/AI | `agents/`: get `smoke_live.py` green, Reader accuracy, Auditor, Chaser, MCP wiring |
| D Story/Quality | rulebook verification, one real interview, evals, README, blog, video, submission |

## Days
| Day | Goal | Done when |
|---|---|---|
| Thu 8 | Live Reader + deploy skeleton | `smoke_live.py` passes; `run_evals.py --mode live` reads sample bills and quotes; API deployed; UI on Amplify |
| Fri 9 | Plan + Auditor live | live Reader feeds the same tools; quote verdicts match expected; trace panel shows live tool calls |
| Sat 10 | Loop | time-machine wakes the Chaser; DISCOM reply produces Plan v2; arena replays the real negotiation drafts |
| Sun 11 | Ship | feature freeze at noon; video; README; blog; submit 3+ hours early; links open in a private window |

## Hero moments (protect these)
1. The quote audit catching the trap (and ignoring the hidden instruction).
2. The time jump to a stalled DISCOM, escalation draft, human approval.
3. The DISCOM reply that changes the plan (v1 to v2).

## Cut list (cut from the bottom first)
Local-language audio, WhatsApp-chat reader, terrace photo scout, satellite roof detection, digital twin, voice, real portal filing, payments, multi-state rules. 3D is not planned: keep the arena 2D/2.5D.

## Definition of done for any feature
Has a test or an eval number, is labelled if simulated, cites the rulebook if it states a rule.
