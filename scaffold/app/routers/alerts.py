from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.price_alert import PriceAlert
from app.schemas import PriceAlertOut

router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# Refer to the API Endpoint Reference / FR-4.2 in ASSESSMENT-BRIEF.md.
# ─────────────────────────────────────────────────────────────────────────────


# GET /alerts
# List alerts, filterable by ?commodity_id=, paginated.
@router.get("/", response_model=list[PriceAlertOut])
def list_alerts(
    commodity_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    query = db.query(PriceAlert)
    if commodity_id is not None:
        query = query.filter(PriceAlert.commodity_id == commodity_id)

    alerts = (
        query.order_by(PriceAlert.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return alerts