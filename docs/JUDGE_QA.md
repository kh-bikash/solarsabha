# Hard questions, honest answers

- **Isn't this a calculator with a chatbot?** Sizing is a small part. The value is reading the society's real documents,
  auditing quotations against the scheme's rules, running a committee decision (letters, approvals, who pays what) and
  following up with the DISCOM for weeks.
- **Does it work on real documents?** Yes. Upload digital PDF bills and quotations: the offline reader extracts the fields
  with plain rules (30/30 on our specimen set: 12 bills and 6 quotations, including a provisional bill, a quote with no price and a hidden instruction). Photos and scans need
  the live AI Reader, or a person types the values in. When the AI reads a PDF, its numbers are checked against
  the plain-rule reader and any disagreement is marked unclear. Every value can be corrected before it is used.
- **Who are the vendors?** In the sample, fictional companies with realistic quotations. The negotiation room is a labelled
  simulation; real negotiation happens by email. The audit runs on whatever quotations the committee uploads.
- **How do you know the rules are right?** Every rule is in a dated rulebook with its source and a status shown in the app.
  We verified it against the MNRE PM Surya Ghar guidelines (June 2024): for example the subsidy is paid only through vendors
  registered on the National Portal, and they owe 5 years of free maintenance. Anything not official is labelled
  "verify" or "our assumption". See `docs/RULEBOOK_VERIFICATION.md`.
- **What if the AI is wrong?** Numbers come from code. The app cannot send, sign, pay or file. People approve every letter,
  and an approval is withdrawn automatically if the letter changes afterwards. "Not verified" is an allowed answer.
- **Prompt injection?** Documents are data. The reader extracts all text, including hidden text; the Auditor scans it for
  instruction-like phrases, ignores them and flags the quote red. No tool exists that an injected instruction could misuse.
- **Is the AI running in this demo?** Yes, on Gemini. Ask the agents to review runs the Secretary, which calls the Auditor
  and the Chaser (agents as tools) with our SolarRules MCP tools; the Chaser reads DISCOM emails; letters can be polished
  with a facts check. The header says which model family is in use, and the review says which model answered.
- **What if the free AI quota runs out mid-demo?** Each call moves down a chain of seven Gemini models, then to
  BazaarLink for the text agents. If all are out, reading falls back to the plain-rule reader and the screen says so; the
  plan, audit, letters and timeline never depend on the AI.
- **Why not Bedrock?** It is supported by one deployment parameter (`ModelProvider=bedrock`, India-only profile). Our new
  AWS account is not yet allowed to call it, and the organisers confirmed Bedrock is not required.
- **Is it deployed?** Yes: https://solarsabha.d2vnrqt0vyz925.amplifyapp.com on Amplify, with API Gateway, Lambda, DynamoDB,
  S3, EventBridge Scheduler and SSM Parameter Store in Mumbai. Creating a project sets a real alarm for the Chaser.
- **A review takes minutes; doesn't API Gateway time out?** The API Lambda starts the review as a background invocation of
  itself and returns at once; the page polls. Every save is versioned, so the background job and a person's edit can't
  overwrite each other.
- **Who can see a society's data?** Only people with its link (a random access key; only a hash is stored). Roles limit who
  can change or approve. Projects expire after a year and can be exported or deleted at any time. See `docs/PRIVACY.md`.
- **Why multiple agents?** Small focused jobs that can be tested separately. The Planner is plain code, not an agent, on purpose.
- **Real impact?** kW installed and tonnes of CO2 avoided (CEA factor 0.710 t/MWh), plus days saved by chasing on time. In the
  hackathon these are computed for the sample society, not measured outcomes.
