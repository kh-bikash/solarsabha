# Architecture

```
Committee (browser)
   |  React app (Amplify Hosting)                       2.5D arena, trace panel, drafts queue
   v
API Gateway (HTTP API) --> ApiFunction (Lambda, solarsabha.handlers.api)
                              |-- offline pipeline: plain-code tools (rulebook, sizing, audit, timeline)
                              |-- (live mode) Strands agents on Bedrock: Reader (multimodal), Auditor, Chaser, Secretary
                              |       '-- SolarRules MCP server (rules + calculators)
                              '-- state: DynamoDB (pk=PROJECT#id, sk=STATE)
S3: uploaded bills/quotes + generated documents
EventBridge Scheduler --> WakeFunction (solarsabha.handlers.wake): "wake me on day 21 and check the DISCOM"
(Optional upgrade) Step Functions with a wait-for-callback step for long human waits
SES: approved drafts (NOT wired in this build; there is no send function)
```

## How the agent "waits" weeks
Agents run for seconds. Between steps the project lives in DynamoDB. A one-time EventBridge schedule wakes `WakeFunction`, which reloads the project, re-runs the Chaser logic (`tools/timeline.py`), and writes any new drafts. In the demo, `POST /projects/{id}/advance` moves a SIMULATED clock and runs the same code path.

## Plain code vs AI
| Plain code (tested, exact) | AI (judgement, language) |
|---|---|
| sizing, money, CO2, fairness, price per kW, timeline status, chase level, drafts' facts | reading bills and quotes (vision), explaining flags in plain words, polishing draft wording, classifying messy DISCOM replies, deciding what to ask next |

## Agents as tools
The Secretary calls specialists through `Agent.as_tool(...)` (Strands). The Planner is NOT an agent: it is code (`tools/sizing.py`), exposed as tools.

## Modes
- **Offline** (`pipeline.run_offline`): no LLM. Reading values come from `samples/society.json`.
- **Live**: Reader extracts from real PDFs/images; Auditor and Secretary explain; numbers still come from the same tools.

## Known gaps (be honest in the video)
Live agents not run against Bedrock in this repo; no real vendor or DISCOM integration; the approved-vendor list is a sample; SES sending and Step Functions callback flow are described, not built.
