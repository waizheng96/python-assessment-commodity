from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_trader

router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# TODO: Implement the endpoints below.
# Refer to the API Endpoint Reference / FR-4.3, FR-4.4 in ASSESSMENT-BRIEF.md.
# See python-learning-guide.md Day 4 for the openpyxl export pattern.
# ─────────────────────────────────────────────────────────────────────────────


# POST /reports
# Generate an Excel report for the requesting trader's CURRENT WATCHLIST
# (not an arbitrary commodity list) over a date range: raw prices, 5-day and
# 10-day moving averages, % change, highlighted alert rows.
# BUSINESS RULE: the trader's watchlist must contain at least one commodity
#   — return 400 ("add a commodity to your watchlist first").
# BUSINESS RULE: a commodity with fewer than 5 snapshots in range is included
#   in the report with raw prices only, noted rather than excluded/failed.
@router.post("/")
def generate_report(db: Session = Depends(get_db), acting_trader=Depends(get_current_trader)):
    # TODO
    return {"message": "Not implemented"}


# GET /reports
# List previously generated reports, paginated.
@router.get("/")
def list_reports(db: Session = Depends(get_db)):
    # TODO
    return {"message": "Not implemented"}


# GET /reports/{report_id}/download
# Stream the generated .xlsx file.
# BUSINESS RULE: if the file is missing, return 404 — not a corrupt empty file.
@router.get("/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db)):
    # TODO
    return {"message": "Not implemented"}
