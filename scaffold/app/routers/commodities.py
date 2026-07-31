import os
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.commodity import Commodity
from app.models.price_alert import PriceAlert
from app.models.price_snapshot import PriceSnapshot
from app.schemas import CommodityOut, PriceSnapshotCreate, PriceSnapshotOut

router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# Refer to the Data Model / API Endpoint Reference / FR-2, FR-4.1 in ASSESSMENT-BRIEF.md.
# ─────────────────────────────────────────────────────────────────────────────

THRESHOLD_METALS_AGRI_PCT = Decimal(os.environ.get("THRESHOLD_METALS_AGRI_PCT", "1.5"))
THRESHOLD_ENERGY_PCT = Decimal(os.environ.get("THRESHOLD_ENERGY_PCT", "3.0"))


def _threshold_for_desk(desk: str) -> Decimal:
    if desk == "energy":
        return THRESHOLD_ENERGY_PCT
    return THRESHOLD_METALS_AGRI_PCT


# GET /commodities
# List the seeded reference table of tracked commodities (read-only).
@router.get("/", response_model=list[CommodityOut])
def list_commodities(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(Commodity).order_by(Commodity.id).offset(skip).limit(limit).all()


# GET /commodities/{commodity_id}
# Return a single commodity by id.
@router.get("/{commodity_id}", response_model=CommodityOut)
def get_commodity(commodity_id: int, db: Session = Depends(get_db)):
    commodity = db.get(Commodity, commodity_id)
    if commodity is None:
        raise HTTPException(status_code=404, detail="Commodity not found")
    return commodity


# POST /commodities/{commodity_id}/prices
# Record a new price snapshot for a commodity.
@router.post("/{commodity_id}/prices", response_model=PriceSnapshotOut, status_code=201)
def record_price(
    commodity_id: int,
    payload: PriceSnapshotCreate,
    db: Session = Depends(get_db),
):
    commodity = db.get(Commodity, commodity_id)
    if commodity is None:
        raise HTTPException(status_code=404, detail="Commodity not found")

    if payload.price <= 0:
        raise HTTPException(status_code=400, detail="price must be greater than 0")

    captured_at = payload.captured_at
    if captured_at.tzinfo is not None:
        captured_at = captured_at.astimezone(timezone.utc).replace(tzinfo=None)

    previous = (
        db.query(PriceSnapshot)
        .filter(PriceSnapshot.commodity_id == commodity_id)
        .order_by(PriceSnapshot.captured_at.desc())
        .first()
    )

    if previous is not None and captured_at <= previous.captured_at:
        raise HTTPException(
            status_code=400,
            detail="captured_at must be after the commodity's most recent snapshot",
        )

    snapshot = PriceSnapshot(
        commodity_id=commodity_id,
        price=payload.price,
        captured_at=captured_at,
        source=payload.source,
    )
    db.add(snapshot)
    db.flush()  # assigns snapshot.id without committing yet

    # FR-4.1: desk-dependent threshold alert computation
    if previous is not None:
        pct_change = ((snapshot.price - previous.price) / previous.price) * Decimal(100)
        threshold = _threshold_for_desk(commodity.desk)

        if abs(pct_change) > threshold:
            alert = PriceAlert(
                commodity_id=commodity_id,
                price_snapshot_id=snapshot.id,
                pct_change=pct_change,
                threshold_used=threshold,
                threshold_breached=True,
            )
            db.add(alert)

    db.commit()
    db.refresh(snapshot)
    return snapshot


# GET /commodities/{commodity_id}/prices
# List price history for a commodity, paginated, most recent first.
@router.get("/{commodity_id}/prices", response_model=list[PriceSnapshotOut])
def list_prices(
    commodity_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    commodity = db.get(Commodity, commodity_id)
    if commodity is None:
        raise HTTPException(status_code=404, detail="Commodity not found")

    return (
        db.query(PriceSnapshot)
        .filter(PriceSnapshot.commodity_id == commodity_id)
        .order_by(PriceSnapshot.captured_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )