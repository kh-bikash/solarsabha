# Hard questions, honest answers

- **Isn't this a calculator with a chatbot?** Sizing is a small part. The value is reading the society's real documents,
  auditing quotations against the scheme's rules, running a committee decision (letters, approvals, who pays what) and
  following up with the DISCOM for weeks.
- **Does it work on real documents?** Yes. Upload digital PDF bills and quotations: the offline reader extracts the fields
  with plain rules (30/30 on our specimen set: 12 bills and 6 quotations, including a provisional bill, a quote with no price and a hidden instruction). Photos and scans need
  the live Bedrock Reader, or a person types the values in. Every value can be corrected before it is used.
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
- **Is the AI running in this demo?** Our new AWS account is still restricted from Bedrock ("Operation not allowed" on the
  Free plan), so the deployed app runs the offline reader and says so on screen. The live path is built and wired into the
  app: Ask the agents to review runs the Secretary, which calls the Auditor and the Chaser (agents as tools) with our
  SolarRules MCP tools; the Chaser reads DISCOM emails; letters can be polished with a facts check. It is tested with fake
  models and reaches the real Bedrock API, which currently refuses. It switches on with `ReaderMode=live`.
- **Is it deployed?** Yes: https://main.d2vnrqt0vyz925.amplifyapp.com on Amplify, with API Gateway, Lambda, DynamoDB, S3 and
  EventBridge Scheduler in Mumbai. Creating a project sets a real alarm for the Chaser.
- **Who can see a society's data?** Only people with its link (a random access key; only a hash is stored). Roles limit who
  can change or approve. Projects expire after a year and can be exported or deleted at any time. See `docs/PRIVACY.md`.
- **Why multiple agents?** Small focused jobs that can be tested separately. The Planner is plain code, not an agent, on purpose.
- **Real impact?** kW installed and tonnes of CO2 avoided (CEA factor 0.710 t/MWh), plus days saved by chasing on time. In the
  hackathon these are computed for the sample society, not measured outcomes.
