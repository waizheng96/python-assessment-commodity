from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

# ─────────────────────────────────────────────────────────────────────────────
# TODO: Complete each Pydantic schema below.
#
# Naming convention:
#   <Entity>Create — fields accepted on POST
#   <Entity>Update — fields accepted on PUT (all optional)
#   <Entity>Out     — fields returned in responses (config: from_attributes=True)
# ─────────────────────────────────────────────────────────────────────────────


# ── Trader ───────────────────────────────────────────────────────────────────
class TraderCreate(BaseModel):
    # TODO: name: str, email: EmailStr, desk: str (one of "metals","energy","agriculture")
    pass


class TraderUpdate(BaseModel):
    # TODO: all fields optional — name, email, desk, active
    pass


class TraderOut(BaseModel):
    # TODO: id, name, email, desk, active, created_at
    class Config:
        from_attributes = True


# ── Commodity ────────────────────────────────────────────────────────────────
class CommodityOut(BaseModel):
    # TODO: id, symbol, name, unit, desk, is_active
    class Config:
        from_attributes = True


# ── Price Snapshot ───────────────────────────────────────────────────────────
class PriceSnapshotCreate(BaseModel):
    # TODO: price: float (must be > 0 — enforce in the router), captured_at: datetime, source: str
    pass


class PriceSnapshotOut(BaseModel):
    # TODO: id, commodity_id, price, captured_at, source
    class Config:
        from_attributes = True


# ── Watchlist ────────────────────────────────────────────────────────────────
class WatchlistItemCreate(BaseModel):
    # TODO: commodity_id: int
    pass


class WatchlistItemOut(BaseModel):
    # TODO: id, trader_id, commodity_id, added_at
    class Config:
        from_attributes = True


# ── Price Alert ──────────────────────────────────────────────────────────────
class PriceAlertOut(BaseModel):
    # TODO: id, commodity_id, price_snapshot_id, pct_change, threshold_used,
    #       threshold_breached, created_at
    class Config:
        from_attributes = True


# ── Report ───────────────────────────────────────────────────────────────────
class ReportCreate(BaseModel):
    # TODO: date_from: date, date_to: date
    # Note: unlike the treasury domain, this does NOT take an explicit
    # commodity/pair list — the report always covers the requesting trader's
    # current watchlist (see FR-4.3 in ASSESSMENT-BRIEF.md).
    pass


class ReportOut(BaseModel):
    # TODO: id, trader_id, date_from, date_to, filename, row_count, generated_at
    class Config:
        from_attributes = True
