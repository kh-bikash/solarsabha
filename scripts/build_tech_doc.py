"""Build docs/SolarSabha_Technical_Guide.pdf: how the whole system works, for someone joining the project.

    python scripts/build_tech_doc.py

Facts here are kept in line with the code (backend/solarsabha, infra/template.yaml); rebuild after changing either."""
from datetime import date
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (CondPageBreak, KeepTogether, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

OUT = Path(__file__).resolve().parents[1] / "docs" / "SolarSabha_Technical_Guide.pdf"

INK = colors.HexColor("#1f2a3c")
MUTED = colors.HexColor("#5b6678")
ACCENT = colors.HexColor("#2f7d4f")          # Track 03 green
LINE = colors.HexColor("#c9d1dc")
SOFT = colors.HexColor("#f2f5f8")
C_AWS = colors.HexColor("#fff4e0")
C_AI = colors.HexColor("#ece6f7")
C_WEB = colors.HexColor("#e3f0ff")
C_CODE = colors.HexColor("#e5f4ea")
C_DATA = colors.HexColor("#fdecea")

ss = getSampleStyleSheet()
BODY = ParagraphStyle("body", parent=ss["BodyText"], fontName="Helvetica", fontSize=9.6, leading=13.6, textColor=INK,
                      spaceAfter=5)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=8.4, leading=11, textColor=MUTED)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=8.4, leading=11, spaceAfter=0)
CELLB = ParagraphStyle("cellb", parent=CELL, fontName="Helvetica-Bold")
H1 = ParagraphStyle("h1", parent=BODY, fontName="Helvetica-Bold", fontSize=16, leading=20, textColor=INK,
                    spaceBefore=4, spaceAfter=8, keepWithNext=1)
H2 = ParagraphStyle("h2", parent=BODY, fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=ACCENT,
                    spaceBefore=9, spaceAfter=4, keepWithNext=1)
CODE = ParagraphStyle("code", fontName="Courier", fontSize=8, leading=10.4, textColor=INK, backColor=SOFT,
                      borderPadding=5, leftIndent=4, rightIndent=4, spaceBefore=3, spaceAfter=8)
CAPTION = ParagraphStyle("cap", parent=SMALL, alignment=TA_CENTER, spaceBefore=2, spaceAfter=10)

def p(text):
    return Paragraph(text, BODY)

def bullets(items):
    return [Paragraph(f"&bull;&nbsp;&nbsp;{t}", ParagraphStyle("b", parent=BODY, leftIndent=12, firstLineIndent=-9,
                                                                spaceAfter=2.5)) for t in items]

def table(rows, widths, header=True):
    data = [[Paragraph(str(c), CELLB if (header and i == 0) else CELL) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.4, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
             ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5)]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), SOFT))
    t.setStyle(TableStyle(style))
    return t

def code(text):
    return Preformatted(text.strip("\n"), CODE)

# ---------- diagram helpers ----------

def box(d, x, y, w, h, text, fill=SOFT, bold_first=True, size=7.6):
    d.add(Rect(x, y, w, h, rx=4, ry=4, fillColor=fill, strokeColor=INK, strokeWidth=0.7))
    lines = text.split("\n")
    lh = size + 2.4
    top = y + h / 2 + (len(lines) - 1) * lh / 2 - size / 3
    for i, ln in enumerate(lines):
        font = "Helvetica-Bold" if (i == 0 and bold_first) else "Helvetica"
        d.add(String(x + w / 2, top - i * lh, ln, fontName=font, fontSize=size, fillColor=INK, textAnchor="middle"))

def arrow(d, x1, y1, x2, y2, label="", dashed=False, lx=0, ly=0, color=INK):
    d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=0.8, strokeDashArray=[3, 2] if dashed else None))
    import math
    a = math.atan2(y2 - y1, x2 - x1)
    s = 5
    d.add(Polygon([x2, y2, x2 - s * math.cos(a - 0.4), y2 - s * math.sin(a - 0.4),
                   x2 - s * math.cos(a + 0.4), y2 - s * math.sin(a + 0.4)], fillColor=color, strokeColor=color))
    if label:
        d.add(String((x1 + x2) / 2 + lx, (y1 + y2) / 2 + ly, label, fontName="Helvetica-Oblique", fontSize=6.6,
                     fillColor=MUTED, textAnchor="middle"))

def frame(d, x, y, w, h, title, fill):
    d.add(Rect(x, y, w, h, rx=6, ry=6, fillColor=fill, strokeColor=LINE, strokeWidth=0.8))
    d.add(String(x + 6, y + h - 10, title, fontName="Helvetica-Bold", fontSize=7.2, fillColor=MUTED))

def diagram_architecture():
    d = Drawing(170 * mm, 106 * mm)
    W = 170 * mm
    frame(d, 2, 232, 120, 64, "BROWSER", C_WEB)
    box(d, 10, 240, 104, 40, "React app (Vite)\npixel office + folders\nAmplify Hosting", colors.white)
    frame(d, 140, 4, W - 142, 292, "AWS  ap-south-1 (Mumbai)", C_AWS)
    box(d, 152, 246, 110, 34, "API Gateway\nHTTP API, 20 req/s", colors.white)
    box(d, 152, 160, 110, 50, "solarsabha-api\nLambda, Python 3.12\nrouter, roles, pipeline,\nagents", colors.white)
    box(d, 290, 246, 86, 34, "DynamoDB\nproject records", colors.white)
    box(d, 386, 246, 86, 34, "S3\nuploaded files", colors.white)
    box(d, 386, 168, 86, 34, "SSM Parameter\nStore: AI keys", colors.white)
    box(d, 152, 66, 110, 40, "EventBridge\nScheduler\none alarm per project", colors.white)
    box(d, 290, 66, 110, 40, "solarsabha-wake\nLambda: Chaser\nre-checks timeline", colors.white)
    box(d, 2, 134, 120, 60, "Gemini API (Google)\n7-model fallback chain\n+ BazaarLink backup\n(text only)", C_AI)
    box(d, 2, 54, 120, 50, "Amazon Bedrock\nswitchable by one\nparameter (not in use)", C_AI)
    box(d, 300, 12, 172, 36, "CloudWatch Logs\none JSON line per request, 30 days", colors.white)
    arrow(d, 114, 262, 152, 263)
    d.add(String(62, 234.5, "calls the API over HTTPS", fontName="Helvetica-Oblique", fontSize=6.4, fillColor=MUTED,
                 textAnchor="middle"))
    arrow(d, 207, 246, 207, 210)
    arrow(d, 262, 200, 300, 246)                      # to DynamoDB
    arrow(d, 262, 205, 400, 246)                      # to S3
    arrow(d, 262, 184, 386, 184)                      # to SSM
    d.add(String(330, 188, "read key", fontName="Helvetica-Oblique", fontSize=6.6, fillColor=MUTED, textAnchor="middle"))
    arrow(d, 152, 172, 122, 166)
    d.add(String(137, 196, "agents", fontName="Helvetica-Oblique", fontSize=6.6, fillColor=MUTED, textAnchor="middle"))
    arrow(d, 152, 166, 122, 90, dashed=True)
    arrow(d, 207, 160, 207, 106)
    d.add(String(186, 130, "set alarm", fontName="Helvetica-Oblique", fontSize=6.6, fillColor=MUTED, textAnchor="middle"))
    # the review job: the API Lambda invokes itself asynchronously
    d.add(Line(240, 160, 240, 140, strokeColor=INK, strokeWidth=0.8))
    d.add(Line(240, 140, 256, 140, strokeColor=INK, strokeWidth=0.8))
    arrow(d, 256, 140, 256, 160)
    d.add(String(262, 132, "review job: invokes itself", fontName="Helvetica-Oblique", fontSize=6.6, fillColor=MUTED,
                 textAnchor="start"))
    arrow(d, 262, 86, 290, 86)
    d.add(String(276, 110, "due date", fontName="Helvetica-Oblique", fontSize=6.6, fillColor=MUTED, textAnchor="middle"))
    arrow(d, 345, 106, 333, 246)
    d.add(String(346, 150, "recompute + save", fontName="Helvetica-Oblique", fontSize=6.6, fillColor=MUTED,
                 textAnchor="start"))
    return d

def diagram_agents():
    d = Drawing(170 * mm, 78 * mm)
    box(d, 8, 170, 92, 34, "Committee\n(people decide)", C_WEB)
    box(d, 168, 166, 132, 42, "Sabha Secretary\ncoordinator, writes the review", C_AI)
    box(d, 20, 92, 120, 40, "Reader\nbills + quotes -> fields", C_AI)
    box(d, 175, 92, 120, 40, "Auditor\nexplains quote risk", C_AI)
    box(d, 330, 92, 130, 40, "Chaser\ntimeline, replies, letters", C_AI)
    arrow(d, 100, 187, 168, 187, "asks", ly=5)
    arrow(d, 200, 166, 90, 132, "agent as tool", lx=-30, ly=4)
    arrow(d, 234, 166, 234, 132, "agent as tool", lx=28)
    arrow(d, 270, 166, 380, 132, "agent as tool", lx=36, ly=4)
    box(d, 175, 22, 120, 44, "audit_quote, check_vendor,\nscan_for_injection,\nget_rule", C_CODE, bold_first=False)
    box(d, 330, 22, 130, 44, "build_timeline, next_action,\nclassify_reply, replan,\ndraft_* (draft only)", C_CODE,
        bold_first=False)
    box(d, 330, 166, 130, 42, "size_system, money_summary,\nget_rule", C_CODE, bold_first=False)
    box(d, 20, 22, 120, 44, "SolarRules MCP server\nsame rule tools over MCP\n(stdio, FastMCP)", C_CODE)
    arrow(d, 300, 187, 330, 187)
    arrow(d, 234, 92, 234, 66)
    arrow(d, 395, 92, 395, 66)
    arrow(d, 140, 44, 175, 44, "", dashed=True)
    d.add(String(8, 6, "Purple = AI agents (Strands). Green = plain, tested Python. Agents explain and draft; code does "
                 "every number and every rule check.", fontName="Helvetica", fontSize=6.8, fillColor=MUTED))
    return d

def diagram_fallback():
    d = Drawing(170 * mm, 54 * mm)
    names = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-2.5-flash",
             "gemini-2.5-flash-lite", "flash-lite-latest", "3-flash-preview"]
    x = 6
    for i, n in enumerate(names):
        box(d, x, 120, 62, 28, f"{i + 1}\n{n}", C_AI, size=6.4)
        if i < len(names) - 1:
            arrow(d, x + 62, 134, x + 68, 134)
        x += 68
    box(d, 120, 52, 140, 36, "BazaarLink backup\n(review, replies, letters only)", C_AI)
    box(d, 300, 52, 170, 36, "Plain-rule fallback\noffline reader / rule classifier", C_CODE)
    arrow(d, 440, 120, 230, 88, dashed=True)
    d.add(String(356, 98, "all Gemini models out", fontName="Helvetica-Oblique", fontSize=6.6, fillColor=MUTED,
                 textAnchor="start"))
    arrow(d, 260, 70, 300, 70)
    d.add(String(6, 26, "Per model:  daily quota used -> skip it for the life of the container.   Per-minute limit -> "
                 "wait the time Google states (max 5 s", fontName="Helvetica", fontSize=7, fillColor=INK))
    d.add(String(6, 15, "inside a request, 30 s in the background), retry once, then move on.   Overloaded (503) or a garbled "
                 "tool call -> next model.", fontName="Helvetica", fontSize=7, fillColor=INK))
    d.add(String(6, 4, "Any other error (bad key, bad request) is raised at once: retrying would not help.   Uploaded "
                 "documents are never sent to the backup.", fontName="Helvetica", fontSize=7, fillColor=INK))
    return d

def diagram_review_job():
    d = Drawing(170 * mm, 92 * mm)
    lanes = [("Browser", 40), ("API Lambda (request)", 150), ("API Lambda (background)", 285), ("DynamoDB", 420)]
    for name, x in lanes:
        box(d, x - 50, 236, 100, 20, name, SOFT, size=7)
        d.add(Line(x, 236, x, 46, strokeColor=LINE, strokeWidth=0.8, strokeDashArray=[2, 2]))
    steps = [
        (40, 150, 220, "POST /review"),
        (150, 420, 204, "review_job = running (versioned put)"),
        (150, 285, 188, "Invoke itself, InvocationType=Event"),
        (150, 40, 172, "202 Accepted (well inside 30 s)"),
        (40, 150, 150, "GET /projects/{id} every 3 s (max 10 min)"),
        (285, 285, 0, ""),
        (285, 420, 96, "re-read latest, attach review, put (retry x5 on conflict)"),
        (150, 40, 60, "review_job = done -> page shows the review"),
    ]
    for x1, x2, y, label in steps:
        if x1 == x2:
            continue
        arrow(d, x1, y, x2, y, label, ly=4)
    box(d, 235, 112, 100, 44, "Secretary -> Auditor x3\n-> Chaser (Gemini)\nup to 480 s of AI time", C_AI, size=6.6)
    d.add(String(8, 26, "If the AI fails, review_job = failed with a clear message. A job still 'running' after 600 s is "
                 "treated as dead, so a new review", fontName="Helvetica", fontSize=7, fillColor=INK))
    d.add(String(8, 15, "can start. Lambda's automatic retry of failed async calls is off (MaximumRetryAttempts: 0), so a "
                 "review never runs twice by itself.", fontName="Helvetica", fontSize=7, fillColor=INK))
    return d

def diagram_upload():
    d = Drawing(170 * mm, 42 * mm)
    xs = [6, 96, 186, 290, 390]
    labels = ["Upload\nbase64 JSON, <= 6 MB\nkey + role checked", "Sniff type\nmagic bytes: PDF,\nPNG, JPEG only",
              "Store original\nS3: <project>/<id>-name", "Read fields\nAI (20 s) or rules\ncross-checked", "Merge + recompute\nbills/quotes -> plan,\naudit, drafts"]
    fills = [C_WEB, C_CODE, C_AWS, C_AI, C_CODE]
    for i, (x, lab, f) in enumerate(zip(xs, labels, fills)):
        box(d, x, 56, 84 if i < 3 else 92, 52, lab, f, size=6.8)
        if i < 4:
            arrow(d, x + (84 if i < 3 else 92), 82, xs[i + 1], 82)
    d.add(String(6, 34, "Status of each document:  READ (clean)  |  NEEDS_REVIEW (unclear, provisional, or the two readers "
                 "disagree)  |  NEEDS_ENTRY (nothing readable;", fontName="Helvetica", fontSize=7, fillColor=INK))
    d.add(String(6, 23, "a person types the values).  If the AI read fails for any reason the rule reader answers, so an "
                 "upload is never lost.", fontName="Helvetica", fontSize=7, fillColor=INK))
    d.add(String(6, 6, "Every value read can be corrected in Documents before it is used, and the plan shows which bill "
                 "each number came from.", fontName="Helvetica", fontSize=7, fillColor=INK))
    return d

def diagram_alarm():
    d = Drawing(170 * mm, 40 * mm)
    box(d, 6, 64, 100, 40, "Any save\n(API Lambda)", C_CODE)
    box(d, 136, 64, 112, 40, "alarm.sync(doc)\none-time schedule\nsolarsabha-<id>", C_AWS)
    box(d, 278, 64, 86, 40, "Due date\n08:30 IST", C_AWS)
    box(d, 392, 64, 84, 40, "Wake Lambda\nrecompute, log,\nnext alarm", C_CODE)
    arrow(d, 106, 84, 136, 84)
    arrow(d, 248, 84, 278, 84)
    d.add(String(263, 110, "weeks pass", fontName="Helvetica-Oblique", fontSize=6.6, fillColor=MUTED, textAnchor="middle"))
    arrow(d, 364, 84, 392, 84)
    d.add(Line(434, 64, 434, 44, strokeColor=INK, strokeWidth=0.8))
    d.add(Line(434, 44, 192, 44, strokeColor=INK, strokeWidth=0.8))
    arrow(d, 192, 44, 192, 64, "")
    d.add(String(312, 34, "late? next alarm in 7 days (keeps chasing)", fontName="Helvetica-Oblique", fontSize=6.6,
                 fillColor=MUTED, textAnchor="middle"))
    d.add(String(6, 8, "Nothing runs and nothing is billed while waiting. Deleting a project deletes its schedule. A "
                 "scheduler error is logged and never blocks a save.", fontName="Helvetica", fontSize=7, fillColor=INK))
    return d

# ---------- page furniture ----------

def on_page(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 9.5 * mm, "SolarSabha - Technical Guide")
    canvas.drawRightString(A4[0] - 18 * mm, 9.5 * mm, f"Page {doc.page}")
    canvas.restoreState()

def on_first(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(ACCENT)
    canvas.rect(0, A4[1] - 9 * mm, A4[0], 9 * mm, stroke=0, fill=1)
    canvas.restoreState()
    on_page(canvas, doc)

# ---------- content ----------

def build():
    S = []
    S += [Spacer(1, 12 * mm),
          Paragraph("SolarSabha", ParagraphStyle("t", parent=H1, fontSize=30, leading=34)),
          Paragraph("Technical Guide: how the whole system works", ParagraphStyle("st", parent=H1, fontSize=15,
                                                                                    textColor=ACCENT)),
          Spacer(1, 6 * mm),
          p("SolarSabha is an AI project manager for a housing society's rooftop solar project under <b>PM Surya Ghar: "
            "Muft Bijli Yojana</b>. It reads the society's electricity bills and vendor quotations, sizes the system, "
            "audits the quotations against the scheme's rules, prepares meeting papers and letters, and follows up with "
            "the DISCOM (the electricity company) for weeks. People approve every decision; the app cannot send, sign, "
            "pay or file anything."),
          Spacer(1, 4 * mm),
          table([["Live site", "https://solarsabha.d2vnrqt0vyz925.amplifyapp.com"],
                 ["API", "https://f9x2xp42wg.execute-api.ap-south-1.amazonaws.com"],
                 ["Code", "https://github.com/kh-bikash/solarsabha"],
                 ["AWS", "CloudFormation stack <b>solarsabha</b>, region ap-south-1 (Mumbai)"],
                 ["Built for", "WeMakeDevs x AWS Environmental Hacks, Bharat Builds Tour 2026, Track 03: Waste and Energy"],
                 ["This edition", date.today().strftime("%d %B %Y")]], [32 * mm, 138 * mm], header=False),
          Spacer(1, 8 * mm),
          Paragraph("Contents", H2)]
    toc = ["The big picture", "Run it on your own computer", "One request, start to finish", "The data: one record per project",
           "The plain-code core: numbers and rules", "Reading documents", "The AI agents",
           "Models, quotas and time limits", "Long-running work: reviews and alarms", "The frontend",
           "Security and privacy", "Configuration reference", "Deploying and operating it", "Testing and quality",
           "What happens when something fails", "Limits and next steps", "Glossary"]
    S += [Paragraph(f"{i + 1}.&nbsp;&nbsp;{t}", ParagraphStyle("toc", parent=BODY, leftIndent=6, spaceAfter=1.5))
          for i, t in enumerate(toc)]
    S.append(PageBreak())

    # 1
    S += [Paragraph("1. The big picture", H1),
          p("The app has three layers. The <b>browser</b> runs a React app (the pixel-art office and its folders). "
            "<b>AWS</b> runs a small serverless backend: one API function that does all the work, one wake-up function "
            "for scheduled follow-ups, and managed storage. <b>AI models</b> are called by the API function only for "
            "reading, explaining and wording; every number comes from plain Python."),
          KeepTogether([diagram_architecture(), Paragraph("Figure 1. Components and how they talk to each other.", CAPTION)]),
          table([["Part", "What it does", "AWS name"],
                 ["Amplify Hosting", "Serves the built React app (static files)", "app SolarSabha, branch solarsabha"],
                 ["API Gateway (HTTP API)", "Public HTTPS entry; CORS for the site only; throttled to 20 req/s (burst 50)", "f9x2xp42wg"],
                 ["API Lambda", "Routing, access keys, roles, validation, uploads, pipeline, agents, Word export", "solarsabha-api"],
                 ["Wake Lambda", "Runs when a project's alarm rings; re-checks the timeline; sets the next alarm", "solarsabha-wake"],
                 ["DynamoDB", "One item per project (the whole state as JSON), versioned", "solarsabha-StateTable-..."],
                 ["S3", "Original uploaded files, private and encrypted", "solarsabha-uploadsbucket-..."],
                 ["EventBridge Scheduler", "One-time alarm per project for the Chaser", "solarsabha-&lt;project id&gt;"],
                 ["SSM Parameter Store", "AI keys, encrypted (SecureString)", "/solarsabha/gemini-api-key"],
                 ["CloudWatch Logs", "Request logs, 30-day retention", "/aws/lambda/solarsabha-api"],
                 ["CloudWatch Alarms + SNS", "Six alarms for errors, failed reviews, throttles and 5xx; email via SNS", "solarsabha-* alarms, AlertsTopic"]],
                [36 * mm, 90 * mm, 44 * mm]),
          Spacer(1, 4),
          p("Everything on AWS is defined in one file, <font face='Courier'>infra/template.yaml</font> (AWS SAM). "
            "Nothing was clicked together by hand except the Amplify app and the SSM key.")]
    S.append(CondPageBreak(70 * mm))

    # 2
    S += [Paragraph("2. Run it on your own computer", H1),
          p("No AWS account is needed. Locally the same backend code runs behind a small Python server, projects are "
            "saved as JSON files and uploads go to a local folder. Without an AI key the app runs in <b>offline mode</b> "
            "(the plain-rule reader, no AI); everything else works."),
          Paragraph("You need", H2),
          table([["Tool", "Version", "Check with"],
                 ["Git", "any recent", "git --version"],
                 ["Python", "3.12 (the version AWS Lambda runs)", "python --version"],
                 ["Node.js", "20 LTS or newer (includes npm)", "node --version"],
                 ["Gemini API key (optional)", "free from aistudio.google.com; only for the AI features", "-"]],
                [44 * mm, 76 * mm, 50 * mm]),
          Paragraph("One-time setup", H2),
          p("<b>Windows (PowerShell)</b>"),
          code("""
git clone https://github.com/kh-bikash/solarsabha.git
cd solarsabha
python -m venv .venv
.venv\\Scripts\\Activate.ps1          # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r backend/requirements-dev.txt
cd frontend; npm install; cd ..
copy .env.example .env"""),
          p("<b>macOS / Linux</b>"),
          code("""
git clone https://github.com/kh-bikash/solarsabha.git && cd solarsabha
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements-dev.txt
(cd frontend && npm install)
cp .env.example .env"""),
          p("Then open <font face='Courier'>.env</font>. For offline mode leave <font face='Courier'>GEMINI_API_KEY</font> "
            "empty. For the AI agents, paste <b>your own</b> key after <font face='Courier'>GEMINI_API_KEY=</font> and keep "
            "<font face='Courier'>READER_MODE=live</font>. Never commit .env (git ignores it) and never share a key in "
            "chat; each person should use their own."),
          Paragraph("Every time: two terminals", H2),
          p("<b>Terminal 1, the backend</b> (from the repo folder, with the virtual environment active):"),
          code("""
python scripts/dev_server.py          # prints: API on http://localhost:8787"""),
          p("<b>Terminal 2, the frontend</b>:"),
          code("""
cd frontend
$env:VITE_API_URL="http://localhost:8787"; npm run dev          # Windows PowerShell
VITE_API_URL=http://localhost:8787 npm run dev                   # macOS / Linux"""),
          p("Open <b>http://localhost:5173</b>. Click <i>Open the sample society</i>, or start a new one and upload the "
            "specimen bills and quotations from <font face='Courier'>backend/samples/pdfs</font>. The header shows the "
            "mode: <i>Live agents on Gemini</i> or <i>Offline reader, no AI model</i>."),
          p("<b>Just the look, no backend:</b> run <font face='Courier'>npm run dev</font> in frontend/ without "
            "VITE_API_URL. It opens a read-only walk through the sample (the header says <i>Static demo</i>)."),
          Paragraph("Check that everything works", H2),
          code("""
cd backend; python -m pytest -q; cd ..     # 87 backend tests
python scripts/run_evals.py                 # accuracy scoreboard: 30/30
cd frontend; npm test; cd ..                # 32 frontend tests
python scripts/smoke_live.py                # only with a Gemini key: one real AI call"""),
          Paragraph("If something goes wrong", H2),
          table([["You see", "Do this"],
                 ["'python' or 'npm' is not recognised", "Install Python 3.12 / Node.js, tick 'Add to PATH', open a new terminal"],
                 ["Activate.ps1 cannot be loaded", "Run Set-ExecutionPolicy -Scope CurrentUser RemoteSigned once, then activate again"],
                 ["The header says Static demo", "VITE_API_URL was not set in that terminal; set it and restart npm run dev"],
                 ["The header says Offline reader, no AI model", "No key in .env, or READER_MODE is not live; fix .env and restart the backend"],
                 ["Failed to fetch / network error", "The backend is not running in terminal 1, or it stopped with an error"],
                 ["Address already in use (8787 or 5173)", "Another copy is running; close it (Ctrl+C) or restart the computer"],
                 ["'every configured AI model ... daily free quota'", "The free Gemini tier is used up for today; wait until tomorrow or use a paid key"],
                 ["Start over with empty data", "Stop the backend and delete the .state folder in the repo"]],
                [62 * mm, 108 * mm]),
          p("Local differences from AWS: data in <font face='Courier'>.state/</font> instead of DynamoDB and S3; the key "
            "comes from .env instead of SSM; the agents' review runs inside the request; and the Chaser's real alarms are "
            "off (use the time machine to move the clock).")]
    S.append(CondPageBreak(70 * mm))

    S += [Paragraph("3. One request, start to finish", H1),
          p("Take <b>PUT /projects/{id}/bills</b> (someone edits a bill). The same path applies to every route."),
          table([["Step", "What happens", "Where"],
                 ["1", "The browser sends JSON with two headers: <b>x-project-key</b> (the project's secret) and "
                       "<b>x-actor</b> (the committee member's name)", "frontend/src/api.js"],
                 ["2", "API Gateway checks CORS and the rate limit, then calls the Lambda (payload v2)", "template.yaml"],
                 ["3", "The handler matches the route in a table of (method, path, function, who may call)", "handlers/api.py ROUTES"],
                 ["4", "The project is loaded from DynamoDB with a strongly consistent read; expired projects read as missing", "state.py"],
                 ["5", "The access key is hashed (SHA-256) and compared in constant time with the stored hash", "project.check_key"],
                 ["6", "The actor must be a member with the right role: read = anyone with the key; edit = secretary "
                       "or member; secretary-only for members and delete", "project.require_role"],
                 ["7", "The body is validated with Pydantic (types, limits; 9 MB maximum)", "schemas.py"],
                 ["8", "The change is applied, logged in the project's activity log, and the whole pipeline is re-run", "project.recompute"],
                 ["9", "The Chaser's alarm is moved to the new due date", "alarm.sync"],
                 ["10", "The project is saved with a version check (see section 4)", "state.DynamoStore.put"],
                 ["11", "The response is the full project, minus the key hash; one JSON log line is written", "handlers/api.py"]],
                [11 * mm, 117 * mm, 42 * mm]),
          Paragraph("Errors the browser can get", H2),
          table([["Code", "Meaning"],
                 ["400", "Invalid input (the message lists the fields)"], ["401", "Missing or wrong access key"],
                 ["403", "Not a member, or the role cannot do this"], ["404", "Unknown or expired project / route"],
                 ["409", "Someone else saved a moment ago (the page reloads), or a review is already running"],
                 ["413", "Request too large"], ["422", "AI polishing changed a fact, so it was rejected"],
                 ["502", "No AI model could answer; nothing was changed"], ["500", "Unexpected error; logged with a request id"]],
                [16 * mm, 154 * mm]),
          Paragraph("All routes", H2),
          code("""
GET    /health                               GET  /rules  (rulebook + states)
POST   /projects                             {"sample": true} or society + you + consent; returns the key ONCE
GET    /projects/{id}       DELETE /projects/{id} (secretary, confirm name)     GET .../export
PUT    .../society | bills | quotes | flats | assumptions | events | members
POST   .../documents        GET/DELETE .../documents/{did}
POST   .../discom-reply     DELETE .../discom-reply
PUT    .../drafts/{did}     POST .../drafts/{did}/approve     GET .../drafts/{did}/docx
POST   .../advance {days}   POST .../clock/reset          (simulated clock for the demo)
POST   .../review           POST .../drafts/{did}/polish  (live AI mode only)""")]
    S.append(CondPageBreak(70 * mm))

    # 3
    S += [Paragraph("4. The data: one record per project", H1),
          p("Each project is a single DynamoDB item: <font face='Courier'>pk = PROJECT#&lt;id&gt;</font>, "
            "<font face='Courier'>sk = STATE</font>. The whole project is stored as one JSON document in the "
            "<font face='Courier'>doc</font> attribute, next to a <font face='Courier'>version</font> number and a "
            "<font face='Courier'>ttl</font> for automatic deletion. One item per project keeps every save atomic."),
          table([["Field", "Content"],
                 ["id, schema, created_at, updated_at", "10-hex-character id; record format version"],
                 ["key_hash", "SHA-256 of the access key. The key itself is shown once and never stored"],
                 ["consent, expires_at", "Privacy consent (notice version 2026-10c) and the retention deadline"],
                 ["members", "Names and roles: secretary, member, viewer"],
                 ["inputs", "Society details, bills, quotes, flat areas, AGM date"],
                 ["assumptions", "Committee overrides: tariff, cost per kW, yield, share of load"],
                 ["documents", "Each upload: status, which reader, notes, fields read, S3 name"],
                 ["events, started_on, sim_offset_days", "Real dates each stage was done; the demo's simulated offset"],
                 ["discom_reply, reply_reading", "The pasted DISCOM email and how it was read"],
                 ["draft_state", "Edits and approvals, keyed by a stable draft id, with content hashes"],
                 ["review, review_job", "The agents' last review and the background job's status"],
                 ["audit", "Activity log: who did what and when (last 500 entries)"],
                 ["result", "The latest pipeline output: plan, audit, timeline, drafts, trace, rulebook"],
                 ["alarm_at, version", "Next Chaser wake-up; the optimistic-lock counter"]],
                [52 * mm, 118 * mm]),
          Paragraph("Versioned saves (optimistic locking)", H2),
          p("Two things can change a project at the same time: a person's edit and a background review that takes "
            "minutes. Without protection, the slower one would silently overwrite the other. So every record carries a "
            "<b>version</b>. A save says \"write this only if the stored version is still N\" (a DynamoDB conditional "
            "write: <font face='Courier'>ConditionExpression: version = :v</font>) and stores N+1. If someone saved in "
            "between, the write is refused with <b>ConflictError</b>:"),
          *bullets(["A person's request gets <b>409</b>; the page reloads the project and asks them to try again.",
                    "The background review and the wake-up re-read the latest record and retry (up to 5 times), so their "
                    "result is merged instead of lost.",
                    "Locally the same rule is applied to JSON files, so tests catch lost updates too."]),
          Paragraph("Files and retention", H2),
          p("Originals go to S3 as <font face='Courier'>&lt;project id&gt;/&lt;doc id&gt;-&lt;safe name&gt;</font>. "
            "Projects expire after <b>365 days</b> (RetentionDays): DynamoDB TTL deletes the item and an S3 lifecycle rule "
            "expires the files. Deleting a project removes its item, its files and its alarm at once. Point-in-time "
            "recovery is on for the table.")]
    S.append(CondPageBreak(70 * mm))

    # 4
    S += [Paragraph("5. The plain-code core: numbers and rules", H1),
          p("<font face='Courier'>pipeline.py</font> is the heart of the product: a <b>pure function</b> from inputs "
            "(bills, quotes, events, assumptions, DISCOM reply) to a result (plan, audit, fairness table, timeline, next "
            "action, letters, trace). It uses no AI and no AWS, runs in milliseconds, and is re-run after every change. "
            "The AI never does arithmetic; it calls these functions."),
          Paragraph("The rulebook", H2),
          p("<font face='Courier'>data/rulebook.json</font> holds every rule with its value, source, status "
            "(<i>official</i>, <i>verify</i>, <i>team assumption</i>) and date, plus state overrides. The app shows this "
            "citation next to every flag. Key values:"),
          table([["Rule", "Value", "Status"],
                 ["Subsidy for a society's common facilities (GHS)", "Rs 18,000 per kW (Rs 19,800 in special category states)", "official"],
                 ["Subsidy ceiling", "3 kW per flat, 500 kW per society", "official"],
                 ["Vendor must be registered on the National Portal", "otherwise no subsidy", "official"],
                 ["Free maintenance contract (CMC)", "at least 5 years", "official"],
                 ["Subsidy (CFA) paid within", "15 days of DISCOM approval", "official"],
                 ["Grid emission factor (CEA)", "0.71 t CO2 per MWh", "official"],
                 ["Yield", "1,400 kWh per kW per year", "verify"],
                 ["Share of load to cover; cost; tariff", "85%; Rs 50,000/kW; Rs 7/kWh", "team assumption"],
                 ["Advance payment flag", "above 20%", "team assumption"]],
                [70 * mm, 72 * mm, 28 * mm]),
          Paragraph("Sizing and money", H2),
          code("""
annual_kwh  = sum of the last 12 bills' units
ceiling     = min(flats x 3 kW, 500 kW)            (or the DISCOM's limit after a reply)
kW          = round(annual_kwh x share / 1400), clipped to 1..ceiling
              options: small (60% of load), recommended (85%), large (100%)
cost        = kW x cost_per_kW         subsidy = kW x 18,000
saving/year = kW x 1400 x tariff       payback = (cost - subsidy) / saving
CO2/year    = kW x 1400 / 1000 x 0.71 tonnes"""),
          p("For the sample society this gives 36 kW: Rs 18 lakh cost, Rs 6.48 lakh subsidy, Rs 11.52 lakh net, about "
            "3.3 years simple payback and about 36 tonnes of CO2 avoided a year."),
          Paragraph("Quote audit", H2),
          p("<font face='Courier'>tools/quotes.py</font> checks each quotation and gives a verdict: <b>RED</b> if any red "
            "flag, <b>AMBER</b> if any flag, else <b>GREEN</b>. Missing fields are flagged, never guessed."),
          table([["Flag", "Level", "Why"],
                 ["VENDOR_NOT_VERIFIED", "red", "Not on the registered vendor list: the subsidy would be refused"],
                 ["DOCUMENT_CONTAINS_INSTRUCTIONS", "red", "Hidden or visible text tries to instruct the AI (prompt injection)"],
                 ["PRICE_LOW / PRICE_HIGH / PRICE_MISSING", "amber", "Price per kW outside Rs 42,000 to 58,000, or no price"],
                 ["ADVANCE_HIGH / ADVANCE_MISSING", "amber", "Advance above 20%, or not stated"],
                 ["PAY_BEFORE_APPROVAL", "amber", "Asks for payment before DISCOM approval (subsidy risk)"],
                 ["PRESSURE", "amber", "Pressure tactics such as offers that expire today"],
                 ["SERVICE_SHORT / SERVICE_MISSING / WARRANTY_MISSING", "amber", "Maintenance under 5 years, or terms missing"]],
                [62 * mm, 14 * mm, 94 * mm]),
          Paragraph("Timeline, fairness and letters", H2),
          *bullets(["<b>Timeline:</b> six stages (AGM, portal, DISCOM feasibility, installation, net meter, subsidy) with "
                    "expected durations from the rulebook. Each stage is done, active, upcoming or <b>overdue</b>. "
                    "Overdue by 1 to 7 days means a reminder letter; more than 7 days means an escalation.",
                    "<b>Fairness:</b> who pays what, split equally or by flat area.",
                    "<b>Letters:</b> AGM notice, resolution, vendor clarification, DISCOM reminder and escalation, filled "
                    "from the facts. Editing a letter after approval withdraws the approval (content hash check).",
                    "<b>DISCOM reply:</b> a rule classifier spots a capacity limit (\"can permit only upto 30 kW\"), "
                    "approval or a documents request; a limit produces <b>Plan v2</b> at the new size."])]
    S.append(CondPageBreak(70 * mm))

    # 5
    S += [Paragraph("6. Reading documents", H1),
          KeepTogether([diagram_upload(), Paragraph("Figure 2. What happens to an uploaded bill or quotation.", CAPTION)]),
          Paragraph("Two readers", H2),
          table([["", "Offline reader (reading.py)", "AI reader (agents/reader.py)"],
                 ["Works on", "Digital PDFs (text layer)", "PDFs, photos and scans"],
                 ["How", "pypdf extracts all text, including hidden text; regular expressions find month, units, amount, vendor, price, terms", "Gemini reads the file as a document or image and fills a typed form (BillData / QuoteData)"],
                 ["When", "Always available; the only reader when READER_MODE=offline", "READER_MODE=live; 20 s budget per upload"],
                 ["Cost", "Free, instant", "One model call"]],
                [22 * mm, 74 * mm, 74 * mm]),
          Paragraph("Safety checks on an AI reading", H2),
          *bullets(["<b>Cross-check:</b> on a digital PDF, the AI's numbers are compared with the offline reader's. Any "
                    "disagreement marks the document NEEDS_REVIEW with a note naming the fields.",
                    "<b>Provisional bills:</b> a bill marked provisional (meter not read, units estimated) is flagged.",
                    "<b>Month format:</b> months are normalised (2026-09, Sep-2026, 09/2026 all become 2026-09).",
                    "<b>Hidden text:</b> the offline reader's full text, including white or tiny text, is added to the "
                    "quote so the injection scan sees what the AI might have skipped.",
                    "<b>Documents are data:</b> prompts tell every agent that document text is data, never instructions, "
                    "and an instruction-like phrase turns the quote red."])]
    S.append(CondPageBreak(70 * mm))

    # 6
    S += [Paragraph("7. The AI agents", H1),
          p("The agents are built with the <b>Strands Agents SDK</b> (strands-agents 1.58). Each agent is a model plus a "
            "system prompt plus a small set of tools. They read, explain and draft; they never calculate and cannot act "
            "outside the app."),
          KeepTogether([diagram_agents(), Paragraph("Figure 3. The agent team and the tools each one may use.", CAPTION)]),
          table([["Agent", "Job", "Tools it may call"],
                 ["Sabha Secretary", "Coordinates; writes the committee's review (summary, a question per vendor, next step, what needs a decision, what is not verified)", "reader, auditor, chaser (agents as tools), size_system, money_summary, get_rule"],
                 ["Reader", "Turns a bill or quote into fields", "none (reads the file it is given)"],
                 ["Auditor", "Runs the quote audit and explains each flag in plain words", "audit_quote, check_vendor, scan_for_injection, get_rule"],
                 ["Chaser", "Checks the timeline, reads DISCOM replies, drafts follow-ups, re-plans", "build_timeline, next_action, classify_reply, replan_for_load_limit, draft_discom_reminder, draft_discom_escalation, get_rule"]],
                [26 * mm, 74 * mm, 70 * mm]),
          Paragraph("How a review runs", H2),
          *bullets(["The Secretary gets the project facts as JSON, marked as data. It asks the Auditor about each quote, "
                    "then the Chaser about the timeline, and returns a typed <b>LiveReview</b>.",
                    "<b>Agents as tools:</b> each specialist is exposed to the Secretary as a tool. A fresh specialist is "
                    "built for every call, on the same model the Secretary is using, because a shared agent refuses a "
                    "second call while busy.",
                    "<b>One at a time:</b> the Secretary uses Strands' SequentialToolExecutor, so specialist calls never "
                    "overlap and the trace stays in order.",
                    "<b>Typed answers:</b> every agent returns a Pydantic model (LiveReview, ReplyReading, PolishedLetter, "
                    "BillData, QuoteData). Strands delivers it through a special answer tool."]),
          Paragraph("Guardrails (trace.py, TraceHooks)", H2),
          *bullets(["Before any tool runs, a Strands hook checks it against that agent's allowlist and <b>cancels</b> "
                    "anything else, recording \"Blocked a call\" in the trace. The agent's own answer tool is always "
                    "allowed.",
                    "After a tool runs, its real input and output go into the trace. The office animation and the Logbook "
                    "replay these real events, not a script.",
                    "There is no send, sign, pay or file tool anywhere, so no prompt can make an agent do those things.",
                    "<b>Polish (AI)</b> rewords a letter with a tool-less writer agent; facts_unchanged() compares every "
                    "number, date and reference before and after, and rejects the result (422) if anything changed."]),
          Paragraph("SolarRules MCP server", H2),
          p("<font face='Courier'>backend/mcp_server/solar_rules_server.py</font> serves the rulebook and calculators "
            "(get_rule, list_rules, size_system, money_summary, check_vendor, scan_for_injection) over the Model Context "
            "Protocol (FastMCP, stdio). During a review the server is started as a subprocess and its tools replace the "
            "built-in ones of the same name. If it cannot start in a container, the review continues with the built-in "
            "tools and says so; it is not retried for every model.")]
    S.append(CondPageBreak(70 * mm))

    # 7
    S += [Paragraph("8. Models, quotas and time limits", H1),
          p("<b>MODEL_PROVIDER</b> picks the model behind every agent: <b>gemini</b> (default) or <b>bedrock</b>. "
            "Agents, tools, hooks and prompts are identical either way; only factory.model() changes. Free model quotas "
            "are small, and API Gateway gives up after 30 seconds, so calls go through "
            "<font face='Courier'>run_with_fallback()</font>:"),
          KeepTogether([diagram_fallback(), Paragraph("Figure 4. The model chain. Quota and overload errors move down; "
                                                      "real errors stop.", CAPTION)]),
          Paragraph("Time budgets", H2),
          table([["Where", "AI time allowed", "If it runs out"],
                 ["Reading an upload", "20 s", "The offline reader answers, with a note"],
                 ["Reading a DISCOM reply", "20 s", "The rule classifier answers"],
                 ["Polishing a letter", "20 s", "502 \"did not answer in time\"; the letter is unchanged"],
                 ["The agents' review (background)", "480 s (Lambda timeout 540 s)", "review_job = failed with the reason"]],
                [52 * mm, 48 * mm, 70 * mm]),
          p("A budgeted call runs in a worker thread and is abandoned when its time is up, so the request can still "
            "answer before API Gateway's 30-second cut-off."),
          Paragraph("Error handling details", H2),
          *bullets(["Errors are classified by walking the whole exception chain, because the useful detail (for example "
                    "Google's \"PerDay\" quota id) sits in the underlying error, not in Strands' wrapper.",
                    "Strands' own retries are kept short for Gemini (2 attempts, 2 to 4 s) so a used-up model is "
                    "abandoned quickly; backups get 4 slower attempts.",
                    "If a specialist runs out of quota mid-review, it cancels the Secretary and the error reaches "
                    "run_with_fallback, so the whole review restarts on the next model instead of looping.",
                    "Used-up models are remembered per container (a warm Lambda), so later requests skip them at once."]),
          Paragraph("Where the keys live", H2),
          p("Locally: <font face='Courier'>.env</font> (git-ignored): GEMINI_API_KEY, optional BAZAARLINK_API_KEY. On AWS: "
            "encrypted SSM parameters (<font face='Courier'>/solarsabha/gemini-api-key</font>, optional "
            "<font face='Courier'>/solarsabha/bazaarlink-api-key</font>). The Lambda reads them at run time and may read "
            "only <font face='Courier'>/solarsabha/*</font>. Keys never appear in the template, environment variables, "
            "code, logs or the browser.")]
    S.append(CondPageBreak(70 * mm))

    # 8
    S += [Paragraph("9. Long-running work: reviews and alarms", H1),
          Paragraph("The agents' review runs in the background", H2),
          p("A full review (Secretary, three Auditor calls, Chaser) takes one to three minutes, but API Gateway answers "
            "within 30 seconds. So on AWS the API Lambda starts the review as an <b>asynchronous invocation of itself</b> "
            "and returns at once; the page polls. Locally (dev server) it simply runs inside the request."),
          KeepTogether([diagram_review_job(), Paragraph("Figure 5. The background review job.", CAPTION)]),
          Paragraph("The Chaser's alarm clock", H2),
          p("An agent cannot sit and wait for three weeks, and nothing should run (or be billed) while waiting. So the "
            "Chaser sets an alarm instead:"),
          KeepTogether([diagram_alarm(), Paragraph("Figure 6. How the Chaser follows up for weeks.", CAPTION)]),
          p("The demo's <b>time machine</b> (POST /advance) moves a separate, clearly labelled offset "
            "(sim_offset_days) through the very same recompute, so you can watch a 16-days-late escalation appear without "
            "waiting. Reset returns to the real date.")]
    S.append(CondPageBreak(70 * mm))

    # 9
    S += [Paragraph("10. The frontend", H1),
          p("React 18 built with Vite, in <font face='Courier'>frontend/src</font>. No UI framework: hand-made pixel-art "
            "SVG sprites and plain CSS, themed for Track 03."),
          table([["Piece", "What it does"],
                 ["api.js", "All server calls. LIVE mode when VITE_API_URL is set at build time; MOCK mode (no server, the "
                            "bundled sample, read-only) otherwise. A 409 conflict fires an event that reloads the project."],
                 ["session.js", "Remembers this browser's projects (id + key) in localStorage. A share link carries the key "
                                "in the URL hash (#p=&lt;id&gt;&amp;k=&lt;key&gt;), which browsers never send to servers."],
                 ["office/ and pixel/", "The office scene. story.js turns real trace events into sentences and tells the "
                                        "scene which agent walks where and which object lights up (calculator, filing cabinet, calendar)."],
                 ["components/", "The folders: Welcome, Documents, PlanCard, QuoteTable, Fairness, Timeline, Drafts (your "
                                 "desk), Arena (negotiation simulation), TracePanel (logbook and the agents' review), Settings, PrivacyNotice."],
                 ["App.jsx", "Loads the project, plays new trace events, runs actions, polls the review job every 3 s (up "
                             "to 10 minutes), and shows which model family is live in the header."]],
                [30 * mm, 140 * mm]),
          p("Build for production: <font face='Courier'>VITE_API_URL=&lt;ApiUrl&gt; VITE_PRIVACY_CONTACT=\"...\" npm run "
            "build</font>, then upload <font face='Courier'>dist/</font> to Amplify."),

          Paragraph("11. Security and privacy", H1),
          table([["Concern", "How it is handled"],
                 ["Who can open a project", "Only holders of its link: a random 32-character key; only its SHA-256 hash is "
                                            "stored; compared in constant time"],
                 ["Who can change what", "Roles per member: secretary (everything), member (edit, approve), viewer (read)"],
                 ["Uploads", "6 MB cap, 60 per project, type decided by magic bytes (PDF/PNG/JPEG), file names sanitised"],
                 ["Storage", "DynamoDB and S3 encrypted at rest; bucket private, TLS-only, public access blocked"],
                 ["API", "CORS limited to the site; rate limited; no-store and nosniff headers; key hash never returned"],
                 ["Least privilege", "Each Lambda gets only the permissions it needs (table, bucket, its schedules, /solarsabha/* "
                                     "parameters, invoking itself)"],
                 ["Logs", "One JSON line per request: route, status, time, project id. No document content, no names"],
                 ["Consent and rights", "Privacy notice accepted at creation; export, correction and deletion built in; "
                                        "auto-deletion after a year (DPDP Act, 2023)"],
                 ["AI data", "Gemini processes data outside India; the free tier may be used to improve Google's products, "
                             "so real society data needs a paid key or Bedrock's India-only profile. The backup never receives documents"],
                 ["Actions", "Draft only: no send, sign, pay or file code exists; approvals are named and withdrawn on edit"]],
                [34 * mm, 136 * mm])]
    S.append(CondPageBreak(70 * mm))

    # 11
    S += [Paragraph("12. Configuration reference", H1),
          Paragraph("Environment variables (backend)", H2),
          table([["Variable", "Meaning", "Set by"],
                 ["READER_MODE", "live = AI agents on; anything else = offline reader, no AI", ".env / template"],
                 ["MODEL_PROVIDER", "gemini (default) or bedrock", ".env / template"],
                 ["GEMINI_API_KEY / GEMINI_KEY_PARAM", "Key directly (local) or the SSM parameter name (AWS)", ".env / template"],
                 ["GEMINI_MODEL_ID", "Comma-separated model chain (default: 7 models)", "template"],
                 ["BAZAARLINK_API_KEY / BAZAARLINK_KEY_PARAM", "Optional text-only backup", ".env / template"],
                 ["BEDROCK_MODEL_ID", "Model or inference profile when MODEL_PROVIDER=bedrock", ".env / template"],
                 ["STATE_BACKEND", "dynamodb on AWS; local JSON files otherwise", "template"],
                 ["TABLE_NAME, UPLOADS_BUCKET", "Where state and files go", "template"],
                 ["SCHEDULER_ROLE_ARN, WAKE_FUNCTION_ARN", "Turn on the Chaser's alarms", "template"],
                 ["ALLOWED_ORIGIN", "The site allowed by CORS", "template"],
                 ["RETENTION_DAYS", "Days before a project is deleted (365)", "template"]],
                [58 * mm, 82 * mm, 30 * mm]),
          Paragraph("Template parameters (sam deploy)", H2),
          table([["Parameter", "Current value"],
                 ["ReaderMode", "live"], ["ModelProvider", "gemini"], ["GeminiKeyParam", "/solarsabha/gemini-api-key"],
                 ["GeminiModelChain", "the 7-model default"], ["BazaarlinkKeyParam", "empty (backup off on AWS)"],
                 ["BedrockModelId", "in.anthropic.claude-sonnet-5 (unused while provider is gemini)"],
                 ["AllowedOrigin", "https://solarsabha.d2vnrqt0vyz925.amplifyapp.com"], ["RetentionDays", "365"],
                 ["AlarmEmail", "empty (alarms visible in CloudWatch; no email yet)"]],
                [50 * mm, 120 * mm]),

          Paragraph("13. Deploying and operating it", H1),
          code("""
# backend (Docker Desktop running; --use-container avoids a Windows-only MCP dependency)
cd infra
sam build --use-container
sam deploy --stack-name solarsabha --region ap-south-1 --resolve-s3 --capabilities CAPABILITY_IAM \\
  --parameter-overrides ReaderMode=live ModelProvider=gemini \\
  GeminiKeyParam=/solarsabha/gemini-api-key \\
  AllowedOrigin=https://solarsabha.d2vnrqt0vyz925.amplifyapp.com

# frontend
cd frontend
VITE_API_URL=https://f9x2xp42wg.execute-api.ap-south-1.amazonaws.com npm run build
# zip dist/, then: aws amplify create-deployment -> upload zip -> aws amplify start-deployment

# rotate the AI key (no redeploy needed; a new Lambda container picks it up)
aws ssm put-parameter --region ap-south-1 --type SecureString --overwrite \\
  --name /solarsabha/gemini-api-key --value "NEW_KEY"

# remove everything
sam delete --stack-name solarsabha --region ap-south-1
aws amplify delete-app --app-id d2vnrqt0vyz925 --region ap-south-1"""),
          Paragraph("Where to look in the AWS Console (region Mumbai)", H2),
          table([["To see", "Open"],
                 ["Every resource", "CloudFormation &gt; solarsabha &gt; Resources"],
                 ["Project records", "DynamoDB &gt; Tables &gt; solarsabha-StateTable-... &gt; Explore table items"],
                 ["Uploaded files", "S3 &gt; solarsabha-uploadsbucket-..."],
                 ["Errors and timings", "CloudWatch &gt; Log groups &gt; /aws/lambda/solarsabha-api"],
                 ["Chaser alarms", "EventBridge &gt; Scheduler &gt; Schedules (solarsabha-&lt;id&gt;)"],
                 ["Health alarms", "CloudWatch &gt; Alarms &gt; All alarms (solarsabha-*)"],
                 ["The AI key", "Systems Manager &gt; Parameter Store"]],
                [40 * mm, 130 * mm]),
          Paragraph("Alarms", H2),
          p("Six CloudWatch alarms send to one SNS topic. Handled errors (bad input, wrong key, a 502 when no AI model can "
            "answer) are answered by the API itself, so two log metrics pick out the real problems from the request log."),
          table([["Alarm", "Fires when"],
                 ["solarsabha-unhandled-errors", "An unhandled exception (log metric on unhandled_error), 1 in 5 minutes"],
                 ["solarsabha-review-failures", "3 or more failed agent reviews in an hour (usually every model out of quota)"],
                 ["solarsabha-api-lambda-errors", "The API Lambda crashed or timed out"],
                 ["solarsabha-api-lambda-throttles", "Lambda refused requests for lack of concurrency"],
                 ["solarsabha-wake-lambda-errors", "A scheduled Chaser wake-up failed"],
                 ["solarsabha-api-5xx", "10 or more server errors in 5 minutes at API Gateway"]],
                [50 * mm, 120 * mm]),
          p("For email, redeploy with <font face='Courier'>AlarmEmail=you@example.com</font> and click the confirmation "
            "link AWS sends. Missing data counts as OK, so a quiet night raises nothing."),
          p("<b>Cost:</b> at hackathon traffic everything sits in free allowances (Lambda, API Gateway, on-demand DynamoDB, "
            "S3, Scheduler, standard SSM parameters). Set a zero-spend budget alert in Billing so any charge emails you.")]
    S.append(CondPageBreak(70 * mm))

    # 13
    S += [Paragraph("14. Testing and quality", H1),
          table([["Check", "Command", "Result"],
                 ["Backend unit and API tests: reader, pipeline, roles, privacy, alarms, wake-up, locking, model fallback, "
                  "guardrails, live agents with fake models", "make test", "87 passing"],
                 ["Frontend tests (Vitest)", "make test-ui", "32 passing"],
                 ["Accuracy scoreboard: tools + offline reader on 18 specimen PDFs with known answers", "make evals", "30/30"],
                 ["AWS template lint", "make lint-infra", "clean"],
                 ["Live end-to-end on AWS: AI bill reading, background review, DISCOM reply, polishing", "manual script", "passing"],
                 ["Backend tests, evals, template lint, frontend tests and build, on every push", "GitHub Actions", "green"]],
                [96 * mm, 34 * mm, 40 * mm]),
          p("Agent tests replace the model with fakes that call the real tools, so the wiring, guardrails, structured "
            "answers and fallbacks are tested without spending quota. The specimen documents in "
            "<font face='Courier'>backend/samples/pdfs</font> are fictional and watermarked SPECIMEN; they include a "
            "provisional bill, a quote with no price and a quote with a hidden instruction."),

          Paragraph("15. What happens when something fails", H1),
          table([["Failure", "What the user sees", "Data"],
                 ["Gemini daily quota used up", "Nothing: the next model in the chain answers", "safe"],
                 ["Every model out of quota", "Uploads read by the offline reader with a note; review fails with a clear "
                                              "message; plan, audit, letters, timeline unaffected", "safe"],
                 ["AI slower than 20 s in a request", "The rule-based answer, with a note", "safe"],
                 ["AI reads a number differently from the rules", "Document marked Needs review, naming the fields", "safe"],
                 ["Two people save at once", "The second gets a reload and tries again", "safe (versioned)"],
                 ["Review job's Lambda dies", "After 10 minutes a new review can be started", "safe"],
                 ["MCP server cannot start", "Review runs with built-in tools; noted in the trace", "safe"],
                 ["Scheduler error", "Logged; the save still succeeds", "safe"],
                 ["A quote hides instructions for the AI", "Quote turns RED with the reason", "safe"],
                 ["Unexpected bug", "\"Something went wrong\" with a request id to find in the logs", "unchanged"]],
                [50 * mm, 92 * mm, 28 * mm])]
    S.append(CondPageBreak(70 * mm))

    # 15
    S += [Paragraph("16. Limits and next steps", H1),
          table([["Limit", "Next step"],
                 ["Free Gemini tier: about 20 requests per model per day; content may be used by Google",
                  "A paid key (pennies per review), or Bedrock with the India-only profile once the AWS account allows it"],
                 ["Access is by link, and people pick their own name", "Amazon Cognito sign-in in front of the API"],
                 ["Alarms email nobody until an address is set", "Redeploy with AlarmEmail and confirm the link AWS sends"],
                 ["Only national and special-category rules verified", "Add each state's DISCOM rules once checked"],
                 ["Vendor list, negotiation replies and the sample DISCOM reply are simulated", "Live vendor registry "
                  "lookup; real email threads"],
                 ["Not load-tested", "A short load test before a real launch"]],
                [80 * mm, 90 * mm]),
          Paragraph("17. Glossary", H1),
          table([["Term", "Meaning"],
                 ["PM Surya Ghar", "The national rooftop solar scheme (Muft Bijli Yojana) that pays the subsidy"],
                 ["GHS / RWA", "Group Housing Society / Resident Welfare Association: a society's common facilities"],
                 ["CFA", "Central Financial Assistance: the subsidy itself"],
                 ["DISCOM", "The electricity distribution company: checks feasibility, fits the net meter, inspects"],
                 ["Feasibility", "The DISCOM's check that the local network can take the solar system"],
                 ["Net meter", "A meter that counts electricity both ways, so exported solar is credited"],
                 ["AGM / SGM", "The society's general body meeting, where the project is approved"],
                 ["kW / kWh", "System size / energy. 1 kW of panels makes about 1,400 kWh a year here"],
                 ["CMC", "Comprehensive maintenance contract: 5 years free, required by the scheme"],
                 ["National Portal", "pmsuryaghar.gov.in, where vendors register and societies apply"],
                 ["Strands Agents", "AWS's open-source SDK for building AI agents with tools"],
                 ["MCP", "Model Context Protocol: a standard way to serve tools to AI agents"],
                 ["SAM", "AWS Serverless Application Model: the template that creates the AWS resources"],
                 ["Optimistic locking", "Save only if nobody else saved since you read; otherwise retry"]],
                [34 * mm, 136 * mm])]
    return S

def main():
    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm,
                            bottomMargin=20 * mm, title="SolarSabha Technical Guide", author="SolarSabha team",
                            subject="How SolarSabha works")
    doc.build(build(), onFirstPage=on_first, onLaterPages=on_page)
    print("wrote", OUT)

if __name__ == "__main__":
    main()
