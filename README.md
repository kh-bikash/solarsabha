# SolarSabha

**The AI project manager for a housing society's rooftop solar.**
Built for WeMakeDevs × AWS *Environmental Hacks, Bharat Builds Tour 2026*, **Track 03: Waste and Energy**.

[![CI](https://github.com/kh-bikash/solarsabha/actions/workflows/ci.yml/badge.svg)](https://github.com/kh-bikash/solarsabha/actions/workflows/ci.yml)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue) ![React 18](https://img.shields.io/badge/react-18-blue) ![License: MIT](https://img.shields.io/badge/license-MIT-green)

**Live app: https://solarsabha.d2vnrqt0vyz925.amplifyapp.com** (AWS Amplify, API Gateway, Lambda, DynamoDB, S3, EventBridge Scheduler
and SSM Parameter Store, Mumbai region; the agents run on Gemini).
Open the sample society, or start your own and upload the specimen bills from [`backend/samples/pdfs`](backend/samples/pdfs).
How everything works, end to end: **[Technical guide (PDF)](docs/SolarSabha_Technical_Guide.pdf)**. The problem, the research
and how AI agents work, in plain language: **[Research and learning guide (PDF)](docs/SolarSabha_Research_and_Learning_Guide.pdf)**.

![The SolarSabha office: four agents at work, the committee's desk in front](docs/screenshots/03-office.jpg)

## The problem

An apartment society pays a large electricity bill every month for lifts, water pumps and common lights. Rooftop solar
on the terrace can cut it sharply, and under **PM Surya Ghar: Muft Bijli Yojana** the government pays **Rs 18,000 per kW**
(Rs 19,800 in special category states) for a society's common facilities. Yet most societies never finish the project.

It is not a purchase; it is a months-long process: a committee vote, 50 to 500 flat owners, vendor quotations, a
government portal, and a DISCOM (the electricity company) that must check feasibility, fit a net meter and inspect.
The person running it is a volunteer secretary. **Most projects die of tiredness, not of bad maths.**

## What SolarSabha does

It acts as a patient, well-informed project manager for the committee. People stay in charge of every decision.

| Job | What happens | Who does it |
|---|---|---|
| **Understand** | Reads the common-meter bills (PDF or photo), flags anything unclear, lets a person correct it | Reader |
| **Size** | Sizes the system from real use (not the subsidy ceiling): cost, subsidy, payback, CO2 | plain code |
| **Decide** | Drafts the general body meeting notice, the resolution and who-pays-what tables | Secretary |
| **Choose** | Audits vendor quotations against the scheme's rules and catches hidden instructions | Auditor |
| **Follow** | Tracks the DISCOM for weeks, wakes on an alarm, drafts reminders and escalations, re-plans | Chaser |

**The app can read, calculate, compare, draft and remind. It cannot send, sign, pay or file anything.** Every letter
needs a named committee member's approval, and is downloaded and sent by a person.

## Screenshots

| | |
|---|---|
| ![Welcome](docs/screenshots/01-welcome.jpg) **Welcome.** Open the sample society or start your own (privacy consent required). | ![Office at work](docs/screenshots/02-office-working.jpg) **The office.** Each agent's step plays as it happens; plain-code tools light up as office objects. |
| ![Documents](docs/screenshots/20-uploaded-documents.jpg) **Documents.** Drop bills and quotations; each value is read, shown next to its file and editable. | ![Plan](docs/screenshots/04-plan.jpg) **The plan.** Sized from the bills, with every assumption's source and an editor. |
| ![Quote audit](docs/screenshots/06-quote-audit.jpg) **Quote audit.** Red, amber, green with reasons; each flag cites its rule (text, source, status, date). | ![Who pays](docs/screenshots/07-who-pays.jpg) **Who pays.** Equal split or by flat area. |
| ![Timeline](docs/screenshots/08-timeline.jpg) **Timeline.** Real dates, late stages in red, record progress. | ![Negotiation room](docs/screenshots/09-negotiation-room.jpg) **Negotiation room** (labelled simulation). The unverified vendor gets a proof request, not a haggle. |
| ![Your desk](docs/screenshots/17-approved-letter.jpg) **Your desk.** Formal letters to edit, approve as a named member, and download in Word. | ![Logbook](docs/screenshots/11-logbook.jpg) **Logbook.** What the office did, and what people did. |
| ![Time machine](docs/screenshots/13-time-machine.jpg) **Time machine** (simulated clock). The agents sleep; an alarm wakes the Chaser. | ![Escalation](docs/screenshots/14-chaser-escalation.jpg) **The Chaser wakes**, finds the DISCOM 16 days late and drafts an escalation. |
| ![DISCOM reply](docs/screenshots/15-discom-reply.jpg) **A DISCOM reply** is pasted in; the Chaser reads it. | ![Plan v2](docs/screenshots/16-plan-v2.jpg) **Plan v2**: the DISCOM limits capacity, the plan is redone. |
| ![Settings](docs/screenshots/12-settings.jpg) **Settings.** Members and roles, share link, export, delete. | ![Notice pinned](docs/screenshots/18-notice-pinned.jpg) **Approved notice** pinned on the society notice board. |
| ![Specimen bill](docs/screenshots/specimen-bill.jpg) **Specimen bill** (fictional, watermarked): a provisional month the Reader flags. | ![Specimen quotation](docs/screenshots/specimen-quote.jpg) **Specimen quotation** (fictional, watermarked). |

<p align="center"><img src="docs/screenshots/23-mobile.jpg" width="260" alt="SolarSabha on a phone"></p>

## How it works

### Architecture

```mermaid
flowchart LR
  subgraph Browser["Committee's browser"]
    UI["React app<br/>pixel office + folders"]
  end
  subgraph AWS["AWS ap-south-1"]
    APIGW["API Gateway<br/>HTTP API"]
    API["API Lambda"]
    WAKE["Wake-up Lambda"]
    DDB[("DynamoDB<br/>projects")]
    S3[("S3<br/>documents")]
    SCHED["EventBridge Scheduler<br/>per-project alarms"]
    SSM["SSM Parameter Store<br/>model keys, encrypted"]
  end
  subgraph Models["AI models (one at a time)"]
    GEM["Gemini<br/>7-model chain"]
    BAK["BazaarLink<br/>text-only backup"]
    BR["Amazon Bedrock<br/>switchable"]
  end
  UI --> APIGW --> API
  API --> DDB & S3
  API -- "review runs in the background" --> API
  API -. "key" .-> SSM
  API -- "live agents" --> GEM
  GEM -. "out of quota" .-> BAK
  API -. "ModelProvider=bedrock" .-> BR
  API -- "set alarm" --> SCHED
  SCHED -- "due date" --> WAKE --> DDB
```

### The agent team

```mermaid
flowchart TB
  C(["Committee"]) <--> SEC["Sabha Secretary<br/>coordinator"]
  SEC -- "agent as tool" --> RDR["Reader"]
  SEC -- "agent as tool" --> AUD["Auditor"]
  SEC -- "agent as tool" --> CHS["Chaser"]
  SEC --> T1["sizing, money, fairness"]
  AUD --> T2["audit_quote, check_vendor"]
  CHS --> T3["timeline, classify_reply, replan, drafts"]
  T1 & T2 & T3 --> RB[("Rulebook<br/>dated, cited, per state")]
```

Agents (Strands Agents SDK) read, explain and draft. **Ordinary, tested code does every calculation and
every rule check.** The Planner is deliberately not an agent. The shared rules and calculators are served by our own
**SolarRules MCP server**, which the agents use when it is available.

In live mode, **Ask the agents to review** runs the Secretary, which calls the Auditor and the Chaser as tools. Their real
tool calls replay in the office and the Logbook; the Auditor's explanation and a question for each vendor appear on the
quote cards; the Chaser's advice appears in the Timeline. The Chaser also reads messy DISCOM emails, and
**Polish (AI)** rewords letters, rejected automatically if any number, date or reference changes.

### Models, quotas and time limits

The model is one setting (`ModelProvider`): **Gemini** by default, **Amazon Bedrock** with one parameter change; the
agents, tools and hooks do not change. Free model quotas run out, and API Gateway gives up after 30 seconds, so:

| Situation | What happens |
|---|---|
| A Gemini model hits its daily or per-minute quota, or is overloaded | the call moves down a chain of 7 Gemini models; a per-minute limit is retried once after Google's stated wait |
| Every Gemini model is out | the text agents (review, DISCOM replies, polishing) move on to BazaarLink if its key is set; documents stay on Gemini |
| A model garbles a tool call or a specialist runs out mid-review | the whole review restarts on the next model, so no half-finished answer is kept |
| Reading an upload or a reply inside a request | 20 seconds of AI time, then the plain-rule reader answers, with a note saying so |
| The agents' review (2 to 3 minutes) | the API Lambda starts it in the background and returns 202; the page polls until it is done |
| Two saves race (a slow review and a person's edit) | every project has a version; DynamoDB conditional writes reject the stale save, which retries or asks the page to reload |
| The AI reads a PDF | its numbers are checked against the plain-rule reader; a disagreement or a provisional bill is marked *unclear* for a person |

### How an agent waits three weeks

```mermaid
sequenceDiagram
  participant P as Committee
  participant API as API Lambda
  participant S as EventBridge Scheduler
  participant W as Wake-up Lambda
  P->>API: records progress (portal application done)
  API->>S: alarm for the day feasibility is due
  Note over S: weeks pass, nothing runs, nothing is billed
  S->>W: wake {project_id}
  W->>W: recompute against today: 16 days late
  W->>S: next alarm in 7 days
  P->>API: opens the app: escalation letter waiting
```

### From a bill PDF to a plan

```mermaid
sequenceDiagram
  participant UI
  participant API
  participant RD as Reader
  participant PL as Pipeline (plain code)
  UI->>API: upload bill (key + role checked, type sniffed, 6 MB cap)
  API->>RD: offline rules, or the AI Reader when live (20 s, then rules)
  RD-->>API: month, units, amount, unclear?
  API->>PL: merge, recompute
  PL-->>UI: plan, audit, drafts, trace (the office replays it)
```

More diagrams (project stages, data model): [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). The full walkthrough (requests,
data, agents, models, background jobs, security, configuration, operations, failure modes):
[docs/SolarSabha_Technical_Guide.pdf](docs/SolarSabha_Technical_Guide.pdf).

## Trust by design

| Rule | How it is enforced |
|---|---|
| AI reads and writes; code calculates | sizing, money, CO2, audit flags and timeline are plain functions with tests |
| Documents are data, never instructions | hidden text is extracted and scanned; an instruction-like phrase turns the quote red |
| Agents only use their own tools | a Strands hook cancels any tool call outside the agent's allowlist and logs it |
| Draft only | there is no send, sign, pay or file function in the codebase |
| Named approvals | approvals record who and when, and are withdrawn if the letter changes |
| Cite the rulebook | every rule shows its value, source, status (official, verify, our assumption) and date |
| Label simulations | the vendor negotiation, the clock and the sample vendor list say so on screen |

The rulebook was checked against the MNRE PM Surya Ghar guidelines (June 2024): for example, subsidy only through vendors
**registered on the National Portal**, a **5-year free maintenance contract**, and subsidy **processed within 15 days**
of DISCOM approval. See [docs/RULEBOOK_VERIFICATION.md](docs/RULEBOOK_VERIFICATION.md).

## Privacy

Per-project access keys (only a hash is stored), roles (secretary, member, viewer), recorded consent, a full activity log,
export and delete, automatic deletion after a year, encryption at rest, and no tracking. Written for India's DPDP Act,
2023. Details: [docs/PRIVACY.md](docs/PRIVACY.md).

## Run it

**Static demo (no server, 1 minute)**: the sample society, read-only.
```bash
cd frontend && npm install && npm run dev        # http://localhost:5173
```

**The full app locally (no AWS needed)**: create societies, upload PDFs, edit, approve, download letters.
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1                       # macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements-dev.txt
cd frontend && npm install && cd ..
python scripts/dev_server.py                     # terminal 1: API on http://localhost:8787
cd frontend && VITE_API_URL=http://localhost:8787 npm run dev   # terminal 2: app on http://localhost:5173
```
On Windows PowerShell, set the variable with `$env:VITE_API_URL="http://localhost:8787"` before `npm run dev`. Step by
step for Windows and macOS, with troubleshooting: section 2 of the
[technical guide](docs/SolarSabha_Technical_Guide.pdf). Try it with the specimen documents in `backend/samples/pdfs/`
(12 bills, 6 quotations).

**With the AI agents**: set `READER_MODE=live` and `GEMINI_API_KEY` in `.env` (optional backup:
`BAZAARLINK_API_KEY`; or `MODEL_PROVIDER=bedrock` with `BEDROCK_MODEL_ID`; see `.env.example`), then
`python scripts/smoke_live.py`. On AWS the keys live in SSM Parameter Store, never in the template or the code.

**Deploy to AWS**: `make deploy` (SAM), then host `frontend/dist` on Amplify. Step by step: [docs/SETUP_AWS.md](docs/SETUP_AWS.md).

## Tests and quality

| Check | Command | Result |
|---|---|---|
| Backend unit + API tests (reader, pipeline, roles, privacy, alarms, wake-up, locking, model fallback, live agents with fake models) | `make test` | 87 passing |
| Frontend tests (Vitest) | `make test-ui` | 32 passing |
| Accuracy scoreboard: tools + offline reader on 18 specimen PDFs (12 bills, 6 quotations: 2 green, 2 amber, 2 red) | `make evals` | 30/30 |
| Deployed API smoke test (S3 upload and read, Word, alarm created and removed) and a browser run on the live site | manual | passing |
| AWS template lint | `make lint-infra` | clean |
| Everything CI runs | `make check` | GitHub Actions on every push |

## API

Every `/projects/{id}` route needs `x-project-key`; routes that change data also need `x-actor` (a committee member allowed to).

| Method and path | Purpose |
|---|---|
| `POST /projects` | `{"sample": true}` or `{"society", "you", "consent": true}`; returns the access key once |
| `GET /projects/{id}` · `GET /projects/{id}/export` · `DELETE /projects/{id}` | read, export all data, delete (secretary) |
| `PUT /projects/{id}/society \| bills \| quotes \| flats \| assumptions \| events \| members` | edit inputs |
| `POST /projects/{id}/documents` · `GET`/`DELETE /projects/{id}/documents/{did}` | upload and read, original, delete |
| `PUT /projects/{id}/drafts/{did}` · `POST .../approve` · `GET .../docx` | edit, approve, Word download |
| `POST /projects/{id}/discom-reply` · `POST .../advance` · `POST .../clock/reset` | DISCOM reply; simulated clock |
| `POST /projects/{id}/review` · `POST .../drafts/{did}/polish` | live mode: the agents' review; AI rewording with a facts check |
| `GET /rules` · `GET /health` | rulebook and states; liveness |

## Repository

```
backend/solarsabha/
  pipeline.py        the whole loop as a pure function (no AWS, no AI)
  project.py         access keys, roles, consent, documents, drafts, clock, audit log
  state.py           DynamoDB / local store with versioned saves (optimistic locking)
  files.py           S3 / local storage for uploaded originals
  reading.py         offline reader for digital PDFs; cross-check with the AI reader
  replan.py          DISCOM reply classifier and Plan v2
  rules.py           rulebook access with state overrides
  trace.py           tool-call trace and the agents' tool guardrail
  alarm.py           EventBridge alarms for the Chaser
  export.py          Word letters with a society letterhead
  schemas.py         request validation
  tools/             sizing, quotes, fairness, negotiation, timeline, drafts (plain code)
  agents/            Strands agents: Secretary, Reader, Auditor, Chaser; model chain; MCP link
  handlers/          API and wake-up Lambdas
  data/rulebook.json dated, cited rules with state overrides
backend/mcp_server/  SolarRules MCP server
backend/samples/     sample society and specimen PDFs (fictional, watermarked)
frontend/src/        React app: office/ (scene), pixel/ (sprites), components/ (folders)
infra/template.yaml  AWS SAM
scripts/             dev server, evals, sample generator, live smoke test, technical guide builder
docs/                technical and research guides (PDF), architecture, agents, privacy, rulebook verification,
                     AWS setup, demo script, judge Q&A
```

## Honest status

| Part | Status |
|---|---|
| Projects, uploads, offline reading, plan, audit, letters, approvals, timeline, roles, privacy controls | Working and tested |
| AWS deployment: Amplify site, API Gateway, Lambdas, DynamoDB, S3, Scheduler alarms | **Live** (link above) and smoke-tested |
| Monitoring | Six CloudWatch alarms (unhandled errors, failed reviews, Lambda errors and throttles, wake-up failures, API 5xx) to an SNS topic; email with `AlarmEmail` |
| Live agents: Secretary calling Auditor and Chaser, Reader on PDFs and photos, AI reply reading, polishing | **Live on the deployment** with Gemini (free tier). When the day's free quota is used up, reading falls back to the plain-rule reader with a note on screen; the text agents can also fall back to BazaarLink once its key is stored in SSM (off on the deployment today). Bedrock is supported by one parameter; our new AWS account is not yet allowed to call it |
| Vendor replies, the sample DISCOM reply, the time machine, the vendor list | Simulated or sample data, labelled on screen |
| State-specific rules | Special-category subsidy loaded; other state rules are added only when verified |
| Identity | Per-project keys and roles; add Cognito for verified sign-in |

## Licence

MIT. Sample society, vendors, DISCOM and documents are fictional.
