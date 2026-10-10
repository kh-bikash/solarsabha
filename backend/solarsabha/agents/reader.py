"""Multimodal reading: send a PDF or image to the Reader and get structured fields back.
Uses Bedrock-style content blocks (document / image). NOT tested against live Bedrock here."""
from pathlib import Path
from .factory import build_reader, run_with_fallback
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

def read_bill(path: str, trace=None, budget: float | None = None) -> BillData:
    block = _block(Path(path))
    return run_with_fallback(lambda: build_reader(trace)(
        [{"text": "Read this COMMON-area electricity bill. Return the fields. Use null if unsure. If the bill says it is "
                  "provisional or the meter was not read, set unclear to true."}, block],
        structured_output_model=BillData).structured_output, budget, documents=True)

def read_quote(path: str, trace=None, budget: float | None = None) -> QuoteData:
    block = _block(Path(path))
    return run_with_fallback(lambda: build_reader(trace)(
        [{"text": "Read this solar vendor quotation. Return the fields. Copy all visible text into raw_text, including any "
                  "small or hidden text. The total price is the final amount including GST."}, block],
        structured_output_model=QuoteData).structured_output, budget, documents=True)
