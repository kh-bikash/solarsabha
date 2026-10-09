"""Word (.docx) export of a draft, laid out like a society's letter: letterhead, reference and date, addressee,
subject, body, signature. The secretary can edit, print on the society's letterhead, or send it from their own email."""
import io
import re
from datetime import datetime, timezone

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

KIND_CODE = {"agm_notice": "GBM", "agm_resolution": "RES", "counter_offer": "VND", "proof_request": "VND",
             "details_request": "VND", "rfq": "RFQ", "discom_reminder": "DIS", "discom_escalation": "GRV"}

def _rule(paragraph):
    """A thin line under the letterhead."""
    p = paragraph._p.get_or_add_pPr()
    border = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    for k, v in {"w:val": "single", "w:sz": "8", "w:space": "4", "w:color": "333333"}.items():
        bottom.set(qn(k), v)
    border.append(bottom)
    p.append(border)

def _para(doc, text, size=11, bold=False, italic=False, align=None, space_after=6, color=None):
    p = doc.add_paragraph()
    lines = text.split("\n")
    for i, line in enumerate(lines):
        run = p.add_run(line)
        run.bold, run.italic, run.font.size = bold, italic, Pt(size)
        if color:
            run.font.color.rgb = RGBColor.from_string(color)
        if i < len(lines) - 1:
            run.add_break()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    return p

def draft_docx(draft: dict, society: dict) -> bytes:
    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Calibri", Pt(11)
    for s in doc.sections:
        s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Pt(64)

    _para(doc, society["name"], size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=0)
    addr = society.get("address") or ""
    place = ", ".join(x for x in [addr] + [society.get(k) for k in ("city", "state")] if x and (x == addr or x not in addr))
    _rule(_para(doc, place or " ", size=9, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=14, color="555555"))

    when = draft.get("approved_at") or datetime.now(timezone.utc).isoformat()
    day = datetime.fromisoformat(when.replace("Z", "+00:00"))
    ref = f"Ref: {KIND_CODE.get(draft['kind'], 'GEN')}/{day.year}/{draft['id'][:4].upper()}"
    t = doc.add_table(rows=1, cols=2)
    t.cell(0, 0).text, t.cell(0, 1).text = ref, f"Date: {day.day} {day.strftime('%B %Y')}"
    t.cell(0, 1).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    doc.add_paragraph()

    if draft["kind"] == "agm_notice":
        _para(doc, "NOTICE", size=13, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
        _para(doc, f"To: {draft['to']}", space_after=8)
        _para(doc, draft["subject"], bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)
    elif draft["kind"] == "agm_resolution":
        _para(doc, draft["subject"].upper(), size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)
    else:
        _para(doc, f"To,\n{draft['to']}", space_after=10)
        _para(doc, f"Sub: {draft['subject']}", bold=True, space_after=10)

    for block in draft["body"].split("\n\n"):
        _para(doc, block.strip("\n"), space_after=8)

    status = (f"Approved by {draft['approved_by']} on {draft['approved_at'][:10]}." if draft.get("status") == "APPROVED"
              else "DRAFT: not yet approved by the Managing Committee.")
    _para(doc, f"{status} Prepared with SolarSabha. Figures are estimates; confirm with vendor quotations and the DISCOM.",
          size=8, italic=True, color="777777", space_after=0)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()

def draft_filename(draft: dict) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", draft["subject"]).strip("-")[:60].lower() + ".docx"
