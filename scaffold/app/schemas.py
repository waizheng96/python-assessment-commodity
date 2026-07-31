from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

# ─────────────────────────────────────────────────────────────────────────────
# Naming convention:
#   <Entity>Create — fields accepted on POST
#   <Entity>Update — fields accepted on PUT (all optional)
#   <Entity>Out     — fields returned in responses (config: from_attributes=True)
# ─────────────────────────────────────────────────────────────────────────────

Desk = Literal["metals", "energy", "agriculture"]


# ── Trader ───────────────────────────────────────────────────────────────────
class TraderCreate(BaseModel):
    name: str
    email: EmailStr
    desk: Desk


class TraderUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    desk: Optional[Desk] = None
    active: Optional[bool] = None


class TraderOut(BaseModel):
    id: int
    name: str
    email: str
    desk: Desk
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Commodity ────────────────────────────────────────────────────────────────
class CommodityOut(BaseModel):
    id: int
    symbol: str
    name: str
    unit: str
    desk: Desk
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ── Price Snapshot ───────────────────────────────────────────────────────────
class PriceSnapshotCreate(BaseModel):
    price: Decimal
    captured_at: datetime
    source: str

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("price must be greater than 0")
        return v


class PriceSnapshotOut(BaseModel):
    id: int
    commodity_id: int
    price: Decimal
    captured_at: datetime
    source: str

    model_config = ConfigDict(from_attributes=True)


# ── Watchlist ────────────────────────────────────────────────────────────────
class WatchlistItemCreate(BaseModel):
    commodity_id: int


class WatchlistItemOut(BaseModel):
    id: int
    trader_id: int
    commodity_id: int
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Price Alert ──────────────────────────────────────────────────────────────
class PriceAlertOut(BaseModel):
    id: int
    commodity_id: int
    price_snapshot_id: int
    pct_change: Decimal
    threshold_used: Decimal
    threshold_breached: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Report ───────────────────────────────────────────────────────────────────
class ReportCreate(BaseModel):
    date_from: date
    date_to: date

    @field_validator("date_to")
    @classmethod
    def date_to_after_date_from(cls, v: date, info) -> date:
        date_from = info.data.get("date_from")
        if date_from is not None and v < date_from:
            raise ValueError("date_to must be on or after date_from")
        return v


class ReportOut(BaseModel):
    id: int
    trader_id: int
    date_from: date
    date_to: date
    filename: str
    row_count: int
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)