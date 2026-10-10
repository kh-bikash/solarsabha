# Architecture

## Components

```mermaid
flowchart LR
  subgraph Browser["Committee's browser"]
    UI["React app<br/>pixel office + folders"]
  end
  subgraph AWS["AWS (ap-south-1)"]
    APIGW["API Gateway<br/>HTTP API, throttled"]
    API["ApiFunction (Lambda)<br/>solarsabha.handlers.api"]
    WAKE["WakeFunction (Lambda)<br/>solarsabha.handlers.wake"]
    DDB[("DynamoDB<br/>project state, TTL")]
    S3[("S3<br/>uploaded bills and quotes")]
    SCHED["EventBridge Scheduler<br/>solarsabha-&lt,id&gt, alarms"]
    SSM["SSM Parameter Store<br/>/solarsabha/* model keys"]
  end
  GEM["Gemini API<br/>7-model fallback chain"]
  BAK["BazaarLink<br/>text-only backup"]
  UI -- "x-project-key, x-actor" --> APIGW --> API
  API --> DDB
  API --> S3
  API -. "keys" .-> SSM
  API -- "async self-invoke: review job" --> API
  API -- "READER_MODE=live" --> GEM
  GEM -. "all out of quota" .-> BAK
  API -- "set / move alarm" --> SCHED
  SCHED -- "at(due date)" --> WAKE --> DDB
  WAKE -- "next alarm" --> SCHED
```

Inside the API Lambda:

```mermaid
flowchart TB
  R["router + validation<br/>handlers/api.py, schemas.py"] --> PJ["project layer<br/>project.py: keys, roles, consent,<br/>documents, drafts, clock, audit log"]
  PJ --> RD["reader<br/>reading.py (offline rules)<br/>agents/reader.py (live, Strands + Gemini)"]
  PJ --> PL["pipeline.py<br/>pure: inputs in, result out"]
  PL --> T["plain-code tools<br/>sizing, quotes, fairness,<br/>negotiation, timeline, drafts"]
  T --> RB["rulebook.json<br/>national + state overrides"]
  PJ --> EX["export.py<br/>Word letters"]
  PJ --> AL["alarm.py<br/>EventBridge schedules"]
```

## The agents

```mermaid
flowchart TB
  C(["Committee"]) <--> SEC["Sabha Secretary<br/>coordinator"]
  SEC -- "agent as tool" --> RDR["Reader<br/>bills and quotes"]
  SEC -- "agent as tool" --> AUD["Auditor<br/>quote risk"]
  SEC -- "agent as tool" --> CHS["Chaser<br/>timeline, follow-ups"]
  SEC --> T1["size_system, money_summary, get_rule"]
  AUD --> T2["audit_quote, check_vendor, get_rule"]
  CHS --> T3["build_timeline, next_action, classify_reply,<br/>replan_for_load_limit, draft_* (draft only)"]
  MCP["SolarRules MCP server<br/>same tools over MCP"] -.-> SEC
```

The Planner is not an agent: sizing is plain code. Agents read, explain and draft; tools calculate. In the offline mode
the same tools run without a model, and the office shows the same events.

## How the agent waits weeks

```mermaid
sequenceDiagram
  participant P as Person
  participant API as ApiFunction
  participant DB as DynamoDB
  participant S as EventBridge Scheduler
  participant W as WakeFunction
  P->>API: records "Portal application done" (PUT /events)
  API->>DB: save project
  API->>S: alarm at feasibility due date
  Note over S: weeks pass, nothing runs, nothing is billed
  S->>W: {"project_id": "..."} at 08:30 IST
  W->>DB: load, recompute against today
  W->>DB: save, log "Chaser woke: feasibility 16 days late"
  W->>S: next alarm in 7 days
  P->>API: opens the app: escalation letter waiting on the desk
```

The demo's time machine moves a separate, labelled offset (`sim_offset_days`) through the same recompute.

## A document upload

```mermaid
sequenceDiagram
  participant UI
  participant API
  participant F as Files (S3)
  participant RD as Reader
  participant PL as Pipeline
  UI->>API: POST /documents {kind, filename, base64}
  API->>API: check key and role, size, file type (magic bytes)
  API->>F: store original
  API->>RD: offline rules, or the AI Reader when live (20 s budget, then rules; cross-checked)
  RD-->>API: fields + READ / NEEDS_REVIEW / NEEDS_ENTRY
  API->>PL: merge into bills/quotes, recompute
  PL-->>API: plan, audit, drafts, trace
  API-->>UI: project, the office replays the new events
```

## Project stages

```mermaid
stateDiagram-v2
  [*] --> AGM: committee starts
  AGM --> PORTAL: resolution passed
  PORTAL --> FEASIBILITY: applied on the National Portal
  FEASIBILITY --> INSTALL: DISCOM approves
  FEASIBILITY --> FEASIBILITY: late: reminder (1 to 7 days), escalation (over 7)
  FEASIBILITY --> Replan: DISCOM limits capacity
  Replan --> INSTALL: Plan v2
  INSTALL --> METER: commissioned
  METER --> SUBSIDY: inspection and approval
  SUBSIDY --> [*]: CFA within 15 days of approval
```

## Project record (one DynamoDB item, `pk=PROJECT#<id>`, `sk=STATE`)

| Field | Content |
|---|---|
| `key_hash` | SHA-256 of the access key (never returned) |
| `consent`, `expires_at`, `ttl` | privacy record and retention |
| `members` | names and roles |
| `inputs` | society, bills, quotes, flat areas |
| `assumptions` | committee overrides (tariff, cost, yield, share) |
| `documents` | uploaded files: status, reader, notes, fields |
| `events`, `started_on`, `sim_offset_days` | real dates of progress; simulated offset |
| `discom_reply` | pasted DISCOM email |
| `draft_state` | edits and approvals by stable draft id |
| `audit` | activity log (last 500) |
| `result` | latest pipeline output (plan, audit, timeline, drafts, trace, rulebook) |
| `alarm_at` | when the Chaser wakes next |

## Live agents in the app (READER_MODE=live)

```mermaid
sequenceDiagram
  participant P as Committee member
  participant API as API Lambda
  participant SEC as Sabha Secretary (Gemini)
  participant AUD as Auditor
  participant CHS as Chaser
  participant T as Plain-code tools / SolarRules MCP
  P->>API: POST /review ("Ask the agents to review")
  API-->>P: 202, review_job running (the page polls)
  API->>API: background invocation of itself (no 30 s limit)
  API->>SEC: project facts as JSON (data, not instructions)
  SEC->>AUD: explain each quote
  AUD->>T: audit_quote, check_vendor, get_rule
  SEC->>CHS: what next with the DISCOM?
  CHS->>T: build_timeline, next_action
  SEC-->>API: structured LiveReview (summary, vendor notes, next step, not verified)
  API->>API: save with a version check (retry on conflict)
  API-->>P: review + every tool call with its real output (office replay, Logbook)
```

- `TraceHooks` (Strands hooks) record each tool call with its real output and **cancel any tool outside an agent's allowlist**.
- A DISCOM reply is read by the Chaser agent into a structured `ReplyReading`; if the agent fails, the rule-based reader is used.
- "Polish (AI)" rewords a letter; `facts_unchanged()` rejects the result if any number, date or reference changed.
- Specialists are built fresh for each call and run one at a time, so the trace stays in order.
- Model errors are classified: a daily quota marks the model used up for this container, a per-minute limit waits once,
  an overload or a garbled tool call moves on. If a specialist runs out mid-review, the whole review restarts on the next
  model. BazaarLink joins the end of the chain for text only; documents never go to it.
- If no model can answer, the API returns a clear 502 (or the plain-rule reader answers) and nothing is changed.

## Human checkpoints (guide, Section 17)

| The agent wants to... | Where it is enforced |
|---|---|
| Finalise a size recommendation | Assumptions are shown with their source and edited by the committee; the review lists "needs the committee's decision" |
| Send any message to a vendor or official | Impossible: no send tool exists; `TraceHooks` blocks any tool not on the agent's list; letters need a named member's approval (`approve_draft`), withdrawn if the text changes |
| State that a rule applies | Rule citations show value, source, status and date (`RuleCite`); prompts require `get_rule` |
| Say a vendor is approved | Only `check_vendor` against the loaded list; otherwise "not found"; the list is labelled sample |
| Anything involving money or signatures | No such tool exists anywhere in the codebase |

We use app-level approvals rather than Strands interrupts because approvals happen days later, by a different person,
on a stored letter. An interrupt would have to keep an agent paused across Lambda calls for days.

## Choices against the original tech list
- **Step Functions**: not used. Waiting is done by EventBridge Scheduler alarms and approvals are stored state, so a
  long-running workflow would add moving parts without a job to do.
- **SES**: not used on purpose. The product never sends; people send the downloaded letters.

## Plain code vs AI
| Plain code (tested, exact) | AI (judgement, language) |
|---|---|
| sizing, money, CO2, fairness, price per kW, vendor check, payment-term flags, injection scan, timeline status, chase level, draft facts, offline text reading | reading photos and scans, explaining flags in plain words, polishing draft wording, classifying messy DISCOM replies |
