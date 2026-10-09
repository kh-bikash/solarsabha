"""Structured shapes the Reader must return, so code (not prose) consumes them."""
from typing import Optional
from pydantic import BaseModel, Field

class BillData(BaseModel):
    month: Optional[str] = Field(None, description="YYYY-MM of the billing period")
    units_kwh: Optional[float] = Field(None, description="Units (kWh) consumed on the COMMON-area meter")
    amount_inr: Optional[float] = None
    tariff_inr_per_kwh: Optional[float] = None
    sanctioned_load_kw: Optional[float] = None
    unclear: bool = False
    notes: str = ""

class QuoteData(BaseModel):
    vendor: Optional[str] = None
    capacity_kw: Optional[float] = None
    total_price_inr: Optional[float] = None
    advance_pct: Optional[float] = None
    warranty_panel_years: Optional[float] = None
    service_years: Optional[float] = None
    payment_terms_text: str = ""
    offer_text: str = ""
    raw_text: str = Field("", description="All visible text of the quote, copied verbatim")
    unclear: bool = False
    notes: str = ""

# ---- live agent outputs (the Secretary's review, the Chaser's reading of a reply, a polished letter) ----
from typing import Literal

class VendorNote(BaseModel):
    vendor: str
    explanation: str = Field(description="The audit result in two or three plain sentences, for a busy volunteer")
    question: str = Field(description="One question the committee should ask this vendor")

class LiveReview(BaseModel):
    summary: str = Field(description="What the office did and found, in three to five plain sentences")
    vendor_notes: list[VendorNote] = Field(default_factory=list)
    next_step: str = Field(description="The Chaser's view of what to do next with the DISCOM")
    needs_decision: list[str] = Field(default_factory=list, description="Decisions only the committee can take")
    not_verified: list[str] = Field(default_factory=list, description="Anything that could not be verified")

class ReplyReading(BaseModel):
    type: Literal["LOAD_LIMIT", "APPROVED", "DOCUMENTS_NEEDED", "UNCLEAR"]
    max_kw: Optional[float] = Field(None, description="The capacity limit in kW, only if the DISCOM states one")
    summary: str = Field(description="What the DISCOM said, in one plain sentence")

class PolishedLetter(BaseModel):
    body: str = Field(description="The same letter with clearer wording. Every number, date, name and reference unchanged.")
