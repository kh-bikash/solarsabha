"""Request bodies, validated before anything touches state. Unknown fields are rejected; numbers have sane ranges."""
from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

ROLES = ("secretary", "member", "viewer")
STAGE_KEYS = ("AGM", "PORTAL", "FEASIBILITY", "INSTALL", "METER", "SUBSIDY")

class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class Society(Strict):
    name: str = Field(min_length=2, max_length=120)
    flats: int = Field(ge=1, le=5000)
    city: str = Field("", max_length=80)
    state: str = Field("", max_length=60)
    discom: str = Field("", max_length=120)
    application_ref: str = Field("", max_length=60)
    consumer_no: str = Field("", max_length=40)
    address: str = Field("", max_length=200)

class Member(Strict):
    name: str = Field(min_length=2, max_length=80)
    role: Literal["secretary", "member", "viewer"] = "member"

class CreateProject(Strict):
    sample: bool = False
    society: Optional[Society] = None
    you: Optional[Member] = None
    consent: bool = False

class Bill(Strict):
    month: str = Field(pattern=r"^20\d{2}-(0[1-9]|1[0-2])$")
    units_kwh: float = Field(ge=0, le=10_000_000)
    amount_inr: Optional[float] = Field(None, ge=0, le=1_000_000_000)
    unclear: bool = False
    verified: bool = False
    source_doc: Optional[str] = Field(None, max_length=40)

class Bills(Strict):
    bills: list[Bill] = Field(max_length=60)

    @field_validator("bills")
    @classmethod
    def one_per_month(cls, v):
        months = [b.month for b in v]
        if len(months) != len(set(months)):
            raise ValueError("each month can appear only once")
        return v

class Quote(Strict):
    vendor: str = Field(min_length=1, max_length=120)
    capacity_kw: Optional[float] = Field(None, gt=0, le=10_000)
    total_price_inr: Optional[float] = Field(None, gt=0, le=10_000_000_000)
    advance_pct: Optional[float] = Field(None, ge=0, le=100)
    warranty_panel_years: Optional[float] = Field(None, ge=0, le=50)
    service_years: Optional[float] = Field(None, ge=0, le=50)
    payment_terms_text: str = Field("", max_length=2000)
    offer_text: str = Field("", max_length=2000)
    raw_text: str = Field("", max_length=100_000)
    source_doc: Optional[str] = Field(None, max_length=40)

class Quotes(Strict):
    quotes: list[Quote] = Field(max_length=12)

class Flats(Strict):
    flat_areas_sqft: dict[str, float] = Field(max_length=5000)

    @field_validator("flat_areas_sqft")
    @classmethod
    def areas_ok(cls, v):
        for k, a in v.items():
            if not k or len(k) > 30 or not (50 <= a <= 50_000):
                raise ValueError(f"flat '{k}': name 1-30 characters, area 50-50,000 sq ft")
        return v

class Assumptions(Strict):
    tariff: Optional[float] = Field(None, gt=0, le=50)
    cost_per_kw: Optional[float] = Field(None, ge=10_000, le=500_000)
    yield_kwh_per_kw: Optional[float] = Field(None, ge=600, le=2500)
    share: Optional[float] = Field(None, ge=0.1, le=1.0)

class Members(Strict):
    members: list[Member] = Field(min_length=1, max_length=50)

    @field_validator("members")
    @classmethod
    def has_secretary(cls, v):
        if not any(m.role == "secretary" for m in v):
            raise ValueError("at least one member must be the secretary")
        return v

class Event(Strict):
    stage: Literal["AGM", "PORTAL", "FEASIBILITY", "INSTALL", "METER", "SUBSIDY"]
    done_on: date

class Events(Strict):
    events: list[Event] = Field(max_length=6)

class Advance(Strict):
    days: int = Field(ge=1, le=365)

class DiscomReply(Strict):
    text: str = Field(min_length=5, max_length=10_000)

class DraftEdit(Strict):
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=20_000)
    editor: str = Field(min_length=2, max_length=80)

class Approve(Strict):
    name: str = Field(min_length=2, max_length=80)

class Upload(Strict):
    kind: Literal["bill", "quote"]
    filename: str = Field(min_length=1, max_length=120)
    content_base64: str = Field(min_length=4, max_length=8_500_000)   # about 6 MB of file

class DeleteProject(Strict):
    confirm_name: str = Field(min_length=1, max_length=120)
