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
