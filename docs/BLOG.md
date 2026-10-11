# Solar projects die of tiredness, not bad maths: building SolarSabha

*Draft blog post for the Environmental Hacks submission (Track 03, Waste and Energy). Edit freely; replace the bracketed parts.*

## The problem we picked

Housing societies in India pay a big electricity bill every month for lifts, water pumps and common lights. A solar plant on
the terrace can cut it sharply, and under PM Surya Ghar: Muft Bijli Yojana the government pays Rs 18,000 per kW for a
society's common facilities (Rs 19,800 in special category states). Yet most societies that start never finish.

When we read the scheme guidelines, news reports and vendor guides, the reason was clear: it is not a purchase, it is a
months-long project. A volunteer secretary has to run a general body meeting, collect quotations, apply on the national
portal, and then chase the DISCOM through feasibility, installation, net metering and inspection. Energy think tank IEEFA
found real timelines of 45 to 120 days. [Quote from the society secretary we spoke to.]

## What we built

SolarSabha is a project manager for the committee, shown as a small pixel-art office where four agents work:

- the **Reader** turns bills and quotations into numbers and flags what it is unsure about (a provisional bill, a missing price);
- the **Auditor** checks every quotation against the scheme's rules: is the vendor registered on the National Portal, does
  the price per kW make sense, is there a large advance before DISCOM approval, is the 5-year free maintenance offered,
  and does the document hide instructions aimed at an AI;
- the **Chaser** tracks the DISCOM. It does not "wait" for weeks: it sets an EventBridge alarm for the day a stage is due,
  sleeps, wakes up, and drafts a reminder or an escalation;
- the **Sabha Secretary** coordinates them and talks to the committee.

Everything the committee would actually need is there: meeting notice and resolution in the formal style societies use,
a who-pays-what table, counter-offers, Word downloads with a letterhead, named approvals, real dates, and a log of who did what.

## Decisions we are proud of

**Code calculates, AI reads and writes.** Sizing, subsidy, payback, CO2 and every audit flag are plain functions with
tests. The agents explain, ask and draft. The Planner is deliberately not an agent.

**Documents are data, never instructions.** One of our sample quotations hides white text telling the AI to approve the
vendor. The reader extracts it, the scan flags it, and the quote goes red. Agents also run behind a hook that cancels any
tool call outside their own list.

**Draft only.** There is no send, sign, pay or file function anywhere. Every letter needs a named committee member's
approval, and the approval is withdrawn automatically if the letter changes afterwards.

**A rulebook with receipts.** Every rule has a value, a source, a status and a date, and the app shows them. Checking it
against the MNRE guidelines changed our product: vendors must be *registered* on the National Portal (not "empanelled"),
and they owe five years of free maintenance, so a one-year offer is now flagged.

**Honest labels.** The negotiation room is a labelled simulation. The time machine is a labelled simulated clock. When AI
is off, the app says "Offline reader, no AI model".

## How it runs on AWS

React on Amplify Hosting; API Gateway and two Lambdas (Python 3.12, SAM); DynamoDB with TTL and point-in-time recovery;
an encrypted private S3 bucket; EventBridge Scheduler for the Chaser's alarms; Gemini through the Strands Agents SDK
(Amazon Bedrock is one parameter away), with keys in SSM Parameter Store; our own SolarRules MCP server for the rules and calculators.

## What we measured

- 30/30 on our accuracy scoreboard: the plain-code tools plus the offline reader on 18 specimen documents (12 bills,
  6 quotations with known answers: two green, two amber, two red).
- 87 backend and 32 frontend tests in CI on every push.
- For the sample society: 36 kW, Rs 11.52 lakh after a Rs 6.48 lakh subsidy, about 3.3 years simple payback,
  about 36 tonnes of CO2 avoided a year (CEA factor 0.710 t/MWh). These are computed, not measured outcomes.

## What we would do next

Verified sign-in, state-by-state DISCOM rules, Hindi and other languages, and a pilot with a real housing society.

Live app: https://solarsabha.d2vnrqt0vyz925.amplifyapp.com · Code: https://github.com/kh-bikash/solarsabha
