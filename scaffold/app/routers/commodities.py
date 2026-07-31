from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# TODO: Implement the endpoints below.
# Refer to the Data Model / API Endpoint Reference / FR-2, FR-4.1 in ASSESSMENT-BRIEF.md.
# ─────────────────────────────────────────────────────────────────────────────


# GET /commodities
# List the seeded reference table of tracked commodities (read-only).
@router.get("/")
def list_commodities(db: Session = Depends(get_db)):
    # TODO
    return {"message": "Not implemented"}


# POST /commodities/{commodity_id}/prices
# Record a new price snapshot for a commodity.
# BUSINESS RULE: price must be > 0 — return 400 otherwise.
# BUSINESS RULE: captured_at must be later than the commodity's most recent
#   existing snapshot — return 400 otherwise.
# BUSINESS RULE (FR-4.1, desk-dependent threshold): after inserting the
#   snapshot, compute % change vs. the previous snapshot. Look up the
#   threshold from the commodity's desk (1.5% for metals/agriculture, 3.0%
#   for energy — see .env) and create a PriceAlert if it's exceeded, in the
#   same request.
@router.post("/{commodity_id}/prices")
def record_price(commodity_id: int, db: Session = Depends(get_db)):
    # TODO
    return {"message": "Not implemented"}


# GET /commodities/{commodity_id}/prices
# List price history for a commodity, paginated, most recent first.
@router.get("/{commodity_id}/prices")
def list_prices(commodity_id: int, db: Session = Depends(get_db)):
    # TODO
    return {"message": "Not implemented"}
