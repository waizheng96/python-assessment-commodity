import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
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

EXTERNAL_FETCH_TIMEOUT_SECONDS = float(os.environ.get("EXTERNAL_FETCH_TIMEOUT_SECONDS", "5"))


def _threshold_for_desk(desk: str) -> Decimal:
    if desk == "energy":
        return THRESHOLD_ENERGY_PCT
    return THRESHOLD_METALS_AGRI_PCT


def _create_snapshot_and_alert(
    db: Session,
    commodity: Commodity,
    price: Decimal,
    captured_at: datetime,
    source: str,
) -> PriceSnapshot:
    """Shared logic behind both POST /prices and POST /prices/fetch.

    Applies FR-2.2's validation rules and FR-4.1's desk-dependent alert
    computation, so both entry points stay consistent with each other.
    """
    if price <= 0:
        raise HTTPException(status_code=400, detail="price must be greater than 0")

    if captured_at.tzinfo is not None:
        captured_at = captured_at.astimezone(timezone.utc).replace(tzinfo=None)

    previous = (
        db.query(PriceSnapshot)
        .filter(PriceSnapshot.commodity_id == commodity.id)
        .order_by(PriceSnapshot.captured_at.desc())
        .first()
    )

    if previous is not None and captured_at <= previous.captured_at:
        raise HTTPException(
            status_code=400,
            detail="captured_at must be after the commodity's most recent snapshot",
        )

    snapshot = PriceSnapshot(
        commodity_id=commodity.id,
        price=price,
        captured_at=captured_at,
        source=source,
    )
    db.add(snapshot)
    db.flush()  # assigns snapshot.id without committing yet

    # FR-4.1: desk-dependent threshold alert computation
    if previous is not None:
        pct_change = ((snapshot.price - previous.price) / previous.price) * Decimal(100)
        threshold = _threshold_for_desk(commodity.desk)

        if abs(pct_change) > threshold:
            alert = PriceAlert(
                commodity_id=commodity.id,
                price_snapshot_id=snapshot.id,
                pct_change=pct_change,
                threshold_used=threshold,
                threshold_breached=True,
            )
            db.add(alert)

    db.commit()
    db.refresh(snapshot)
    return snapshot


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
# Record a new price snapshot for a commodity, submitted directly by the caller.
@router.post("/{commodity_id}/prices", response_model=PriceSnapshotOut, status_code=201)
def record_price(
    commodity_id: int,
    payload: PriceSnapshotCreate,
    db: Session = Depends(get_db),
):
    commodity = db.get(Commodity, commodity_id)
    if commodity is None:
        raise HTTPException(status_code=404, detail="Commodity not found")

    return _create_snapshot_and_alert(
        db=db,
        commodity=commodity,
        price=payload.price,
        captured_at=payload.captured_at,
        source=payload.source,
    )


# ── External fetch path (NFR-6) ─────────────────────────────────────────────

class FetchPriceRequest(BaseModel):
    source_url: HttpUrl
    # dotted path into the JSON response where the price lives, e.g. "data.price"
    price_field: str = "price"


@router.post("/{commodity_id}/prices/fetch", response_model=PriceSnapshotOut, status_code=201)
def fetch_price(
    commodity_id: int,
    payload: FetchPriceRequest,
    db: Session = Depends(get_db),
):
    """Fetch a price from an external JSON API and record it as a snapshot.

    BUSINESS RULE (NFR-6): any network/scrape failure — timeout, connection
    refused, non-2xx response, or malformed JSON — must return a clean 502
    or 503, never an unhandled exception / raw 500.
    """
    commodity = db.get(Commodity, commodity_id)
    if commodity is None:
        raise HTTPException(status_code=404, detail="Commodity not found")

    try:
        response = requests.get(
            str(payload.source_url), timeout=EXTERNAL_FETCH_TIMEOUT_SECONDS
        )
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="External price source timed out")
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503, detail="Could not reach external price source"
        )
    except requests.exceptions.RequestException:
        raise HTTPException(
            status_code=502, detail="External price source request failed"
        )

    if response.status_code >= 500:
        raise HTTPException(
            status_code=502,
            detail=f"External price source returned {response.status_code}",
        )
    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"External price source rejected the request ({response.status_code})",
        )

    try:
        body = response.json()
    except ValueError:
        raise HTTPException(
            status_code=502, detail="External price source returned invalid JSON"
        )

    raw_value = body
    for key in payload.price_field.split("."):
        if not isinstance(raw_value, dict) or key not in raw_value:
            raise HTTPException(
                status_code=502,
                detail=f"External price source response missing field '{payload.price_field}'",
            )
        raw_value = raw_value[key]

    try:
        price = Decimal(str(raw_value))
    except (InvalidOperation, TypeError):
        raise HTTPException(
            status_code=502,
            detail="External price source returned a non-numeric price",
        )

    return _create_snapshot_and_alert(
        db=db,
        commodity=commodity,
        price=price,
        captured_at=datetime.now(timezone.utc),
        source=str(payload.source_url),
    )


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