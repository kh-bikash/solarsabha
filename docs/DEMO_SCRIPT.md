# Demo video: recording script (3 minutes)

## Before you record
- **Rehearse offline first, so the AI quota is saved for the real take.** Run the app locally without a Gemini key
  (technical guide, section 2) and click through the script twice. The screens are the same; only the AI parts differ.
- **Record the real take on the live site:** https://solarsabha.d2vnrqt0vyz925.amplifyapp.com
- **Record after 12:30 PM IST.** That is when the free Gemini quota resets, so the AI is most likely to answer.
- One take uses about 20 AI calls. Click **Ask the agents to review** only once per take.
- Screen: 1920x1080, Chrome in a fresh **incognito** window, zoom 110%, bookmarks bar hidden, notifications off
  (Windows: Focus assist on).
- Recorder: OBS, or Windows **Win + Alt + R**. Use a headset mic; record the voice in a quiet room.
- Keep `backend/samples/pdfs/bill_2026-09.pdf` ready in a File Explorer window next to the browser.
- The AI review takes 1 to 3 minutes. **Keep recording and cut the wait out when editing**; the narration never covers it.

## Shot list

| Time | On screen (what to click) | Say |
|---|---|---|
| **0:00-0:15** | Title card: "SolarSabha: the AI project manager for a society's rooftop solar". Or a terrace photo | "Rooftop solar can cut a housing society's electricity bill for lifts and pumps, and under PM Surya Ghar the government pays eighteen thousand rupees per kilowatt. Yet most society projects never finish. They don't fail on maths. They die of tiredness." |
| **0:15-0:30** | The live site. Click **Open the sample society**. In **You are** at the top, pick **Meera (sample)**. Let the office play for a few seconds | "SolarSabha is a patient project manager for the committee. Four AI agents work in this office: a Secretary, a Reader, an Auditor and a Chaser. This is a sample society, so the data is fictional." |
| **0:30-0:50** | Open **Documents**. Drag in `bill_2026-09.pdf`. Wait for it to be read; point at the note on the document | "The committee uploads its electricity bills. The AI Reader reads each one, and plain code checks the AI's numbers. This bill is provisional: the meter wasn't read. So it's flagged for a person to check, not trusted." |
| **0:50-1:05** | Open **The plan**. Point at the kW, the net cost, the payback and the CO2. Hover one assumption to show its source | "The system is sized from the society's real use: thirty-six kilowatts, eleven and a half lakh rupees after the subsidy, paid back in about three years. Every number comes from tested code, not the AI, and every assumption shows its source." |
| **1:05-1:25** | Open **Quote audit**. Show the red quote and its flags. Click a rule citation | "Three vendors quoted. One quotation hides an instruction aimed at the AI. It's ignored, and the quote turns red. The cheapest vendor isn't registered on the National Portal, so the subsidy would be refused. Each flag cites its rule." |
| **1:25-1:50** | Click **Ask the agents to review**. *(cut the wait)* When it's ready, show the office replay, then a vendor question on a quote card, then **Logbook > Agents' review** | "Now the agents review the project. The Secretary asks the Auditor about each quote and the Chaser about the timeline. Every step you see is a real tool call. It ends with one question the committee should ask each vendor." |
| **1:50-2:05** | Open **Your desk**. Open a letter, click **Approve**, then **Word** | "Letters are drafted for the committee, but nothing is ever sent by the app. A named member approves, downloads it, and sends it themselves. If anyone edits the letter later, the approval is withdrawn." |
| **2:05-2:30** | Time machine: click **+25 days** (the screen shows *Simulated clock*). Open **Timeline**, show the late stage in red. Open **Your desk**: the Chaser's new letter | "Real projects wait weeks for the electricity company. The agent doesn't sit and wait: it sets an alarm. Here we fast-forward the clock. The Chaser wakes, sees the DISCOM is late, and drafts a follow-up, waiting on the desk." |
| **2:30-2:45** | Click **A DISCOM reply arrived** > **Use the sample reply** > **Give it to the Chaser**. Show **Plan v2** | "When the DISCOM replies that the transformer can only take a smaller system, the Chaser reads it and the plan is redone at the new size." |
| **2:45-3:00** | The architecture diagram (README or the technical guide PDF). End on the URL and the GitHub link | "Strands agents on Gemini, running on AWS Lambda, DynamoDB, S3 and EventBridge, live in Mumbai. The AI reads and explains, code does the maths, and people approve everything. SolarSabha." |

## If something goes differently
- **The bill is read by the plain-rule reader instead of the AI** (the note says so): keep going and say "The free AI
  quota ran out, so the rule-based reader took over. Nothing else changes."
- **The agents' review fails:** cut that scene, and retake only that part later (after 12:30 PM IST the next day, or
  with a paid key).
- **A click goes wrong:** pause, go back, and redo the scene. Cut between scenes when editing.

## Say what is simulated
Say "sample society" at the start, and "we fast-forward the clock" at the time machine. Don't show the Negotiation room
unless you have time; if you do, say "the vendor replies here are simulated".

## Editing
- Cut every wait (uploads, the review, page loads). The final video should feel brisk.
- Add captions for the key numbers: 36 kW, Rs 11.52 lakh, about 3.3 years, about 36 tonnes of CO2 a year.
- Keep it under 3:00. Export 1080p MP4.
