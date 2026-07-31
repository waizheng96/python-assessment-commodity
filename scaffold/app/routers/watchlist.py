from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_trader
from app.models.commodity import Commodity
from app.models.watchlist_item import WatchlistItem
from app.schemas import WatchlistItemCreate, WatchlistItemOut

router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# Refer to the API Endpoint Reference / FR-3 in ASSESSMENT-BRIEF.md.
#
# This is the domain-unique scoping concept for this assessment — every
# endpoint here operates ONLY on the requesting trader's own rows (identified
# via X-Trader-Id / get_current_trader). This is the isolation test the
# marker specifically checks: Trader A's watchlist must never appear when
# Trader B calls these endpoints with their own header.
# ─────────────────────────────────────────────────────────────────────────────


# POST /watchlist
# Add a commodity to the requesting trader's watchlist.
# BUSINESS RULE: a trader cannot add the same commodity twice — return 400
#   ("already on your watchlist").
@router.post("/", response_model=WatchlistItemOut, status_code=201)
def add_to_watchlist(
    payload: WatchlistItemCreate,
    db: Session = Depends(get_db),
    acting_trader=Depends(get_current_trader),
):
    commodity = db.get(Commodity, payload.commodity_id)
    if commodity is None:
        raise HTTPException(status_code=404, detail="Commodity not found")

    existing = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.trader_id == acting_trader.id,
            WatchlistItem.commodity_id == payload.commodity_id,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=400, detail="already on your watchlist")

    item = WatchlistItem(trader_id=acting_trader.id, commodity_id=payload.commodity_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# GET /watchlist
# Return ONLY the requesting trader's own watchlist.
@router.get("/", response_model=list[WatchlistItemOut])
def get_watchlist(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    acting_trader=Depends(get_current_trader),
):
    return (
        db.query(WatchlistItem)
        .filter(WatchlistItem.trader_id == acting_trader.id)
        .order_by(WatchlistItem.added_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# DELETE /watchlist/{commodity_id}
# Remove a commodity from the requesting trader's watchlist.
# Removing something not on the list returns 404.
@router.delete("/{commodity_id}", status_code=204)
def remove_from_watchlist(
    commodity_id: int,
    db: Session = Depends(get_db),
    acting_trader=Depends(get_current_trader),
):
    item = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.trader_id == acting_trader.id,
            WatchlistItem.commodity_id == commodity_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Commodity not on your watchlist")

    db.delete(item)
    db.commit()
    return None