from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.trader import Trader
from app.models.watchlist_item import WatchlistItem
from app.schemas import TraderCreate, TraderOut, TraderUpdate

router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# Refer to the Data Model / API Endpoint Reference / FR-1 in ASSESSMENT-BRIEF.md.
# ─────────────────────────────────────────────────────────────────────────────


# POST /traders
# Create a new trader.
# BUSINESS RULE: email must be unique — return 400 if it already exists.
@router.post("/", response_model=TraderOut, status_code=201)
def create_trader(payload: TraderCreate, db: Session = Depends(get_db)):
    existing = db.query(Trader).filter(Trader.email == payload.email).first()
    if existing is not None:
        raise HTTPException(status_code=400, detail="email already exists")

    trader = Trader(name=payload.name, email=payload.email, desk=payload.desk)
    db.add(trader)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="email already exists")

    db.refresh(trader)
    return trader


# GET /traders
# List all traders, paginated.
@router.get("/", response_model=list[TraderOut])
def list_traders(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(Trader).order_by(Trader.id).offset(skip).limit(limit).all()


# GET /traders/{trader_id}
# Get one trader or 404.
@router.get("/{trader_id}", response_model=TraderOut)
def get_trader(trader_id: int, db: Session = Depends(get_db)):
    trader = db.get(Trader, trader_id)
    if trader is None:
        raise HTTPException(status_code=404, detail="Trader not found")
    return trader


# PUT /traders/{trader_id}
# Update a trader's fields.
# BUSINESS RULE: `desk` cannot be changed if the trader has a non-empty
# watchlist — return 400 ("clear your watchlist before changing desks").
@router.put("/{trader_id}", response_model=TraderOut)
def update_trader(trader_id: int, payload: TraderUpdate, db: Session = Depends(get_db)):
    trader = db.get(Trader, trader_id)
    if trader is None:
        raise HTTPException(status_code=404, detail="Trader not found")

    updates = payload.model_dump(exclude_unset=True)

    if "desk" in updates and updates["desk"] != trader.desk:
        has_watchlist_items = (
            db.query(WatchlistItem).filter(WatchlistItem.trader_id == trader_id).first()
            is not None
        )
        if has_watchlist_items:
            raise HTTPException(
                status_code=400,
                detail="clear your watchlist before changing desks",
            )

    if "email" in updates and updates["email"] != trader.email:
        existing = db.query(Trader).filter(Trader.email == updates["email"]).first()
        if existing is not None:
            raise HTTPException(status_code=400, detail="email already exists")

    for field, value in updates.items():
        setattr(trader, field, value)

    db.commit()
    db.refresh(trader)
    return trader


# DELETE /traders/{trader_id}
# Not supported — deactivate instead so historical references stay valid.
@router.delete("/{trader_id}", status_code=405)
def delete_trader(trader_id: int):
    return {"detail": "Traders cannot be deleted — set active=false via PUT instead."}