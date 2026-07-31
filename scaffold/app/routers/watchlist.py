from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_trader

router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# TODO: Implement the endpoints below.
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
@router.post("/")
def add_to_watchlist(db: Session = Depends(get_db), acting_trader=Depends(get_current_trader)):
    # TODO
    return {"message": "Not implemented"}


# GET /watchlist
# Return ONLY the requesting trader's own watchlist.
@router.get("/")
def get_watchlist(db: Session = Depends(get_db), acting_trader=Depends(get_current_trader)):
    # TODO
    return {"message": "Not implemented"}


# DELETE /watchlist/{commodity_id}
# Remove a commodity from the requesting trader's watchlist.
# Removing something not on the list returns 404.
@router.delete("/{commodity_id}")
def remove_from_watchlist(commodity_id: int, db: Session = Depends(get_db), acting_trader=Depends(get_current_trader)):
    # TODO
    return {"message": "Not implemented"}
