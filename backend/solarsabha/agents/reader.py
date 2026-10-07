"""Multimodal reading: send a PDF or image to the Reader and get structured fields back.
Uses Bedrock-style content blocks (document / image). NOT tested against live Bedrock here."""
from pathlib import Path
from .factory import build_reader
from .models import BillData, QuoteData

_IMG = {".png": "png", ".jpg": "jpeg", ".jpeg": "jpeg", ".webp": "webp", ".gif": "gif"}

def _block(path: Path) -> dict:
    data, ext = path.read_bytes(), path.suffix.lower()
    if ext == ".pdf":
        # Bedrock document names allow only alphanumerics, spaces, hyphens, parentheses, square brackets
        safe = "".join(c if c.isalnum() or c in " -()[]" else " " for c in path.stem)[:60] or "document"
        return {"document": {"format": "pdf", "name": safe, "source": {"bytes": data}}}
    if ext in _IMG:
        return {"image": {"format": _IMG[ext], "source": {"bytes": data}}}
    raise ValueError(f"Unsupported file type: {ext}")

def read_bill(path: str, trace=None) -> BillData:
    agent = build_reader(trace)
    res = agent([{"text": "Read this COMMON-area electricity bill. Return the fields. Use null if unsure."}, _block(Path(path))],
                structured_output_model=BillData)
    return res.structured_output

def read_quote(path: str, trace=None) -> QuoteData:
    agent = build_reader(trace)
    res = agent([{"text": "Read this solar vendor quotation. Return the fields. Copy all visible text into raw_text."}, _block(Path(path))],
                structured_output_model=QuoteData)
    return res.structured_output
