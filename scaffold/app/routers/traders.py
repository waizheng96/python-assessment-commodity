from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# TODO: Implement the endpoints below.
# Refer to the Data Model / API Endpoint Reference / FR-1 in ASSESSMENT-BRIEF.md.
# ─────────────────────────────────────────────────────────────────────────────


# POST /traders
# Create a new trader.
# BUSINESS RULE: email must be unique — return 400 if it already exists.
@router.post("/")
def create_trader(db: Session = Depends(get_db)):
    # TODO
    return {"message": "Not implemented"}


# GET /traders
# List all traders, paginated.
@router.get("/")
def list_traders(db: Session = Depends(get_db)):
    # TODO
    return {"message": "Not implemented"}


# GET /traders/{trader_id}
# Get one trader or 404.
@router.get("/{trader_id}")
def get_trader(trader_id: int, db: Session = Depends(get_db)):
    # TODO
    return {"message": "Not implemented"}


# PUT /traders/{trader_id}
# Update a trader's fields.
# BUSINESS RULE: `desk` cannot be changed if the trader has a non-empty
# watchlist — return 400 ("clear your watchlist before changing desks").
@router.put("/{trader_id}")
def update_trader(trader_id: int, db: Session = Depends(get_db)):
    # TODO
    return {"message": "Not implemented"}


# DELETE /traders/{trader_id}
# Not supported — deactivate instead so historical references stay valid.
@router.delete("/{trader_id}", status_code=405)
def delete_trader(trader_id: int):
    return {"detail": "Traders cannot be deleted — set active=false via PUT instead."}
