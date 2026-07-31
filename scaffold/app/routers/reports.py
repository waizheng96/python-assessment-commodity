"""Pure business-logic functions for report generation (FR-4.3).

Kept free of DB/HTTP concerns so they can be unit tested directly, per
Deliverable 4 in ASSESSMENT-BRIEF.md.
"""
import os
from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone
from decimal import Decimal
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_trader
from app.models.commodity import Commodity
from app.models.price_alert import PriceAlert
from app.models.price_snapshot import PriceSnapshot
from app.models.report import Report
from app.models.watchlist_item import WatchlistItem
from app.schemas import ReportCreate, ReportOut

router = APIRouter()

MIN_SNAPSHOTS_FOR_AVERAGES = 5
REPORTS_DIR = Path(os.environ.get("REPORTS_DIR", "./generated_reports"))
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class PriceRow:
    captured_at: date
    price: Decimal
    ma_5: Optional[Decimal]
    ma_10: Optional[Decimal]
    pct_change: Optional[Decimal]
    is_alert: bool


@dataclass
class CommodityReportSection:
    symbol: str
    name: str
    rows: list[PriceRow] = field(default_factory=list)
    excluded_note: Optional[str] = None


def moving_average(prices: list[Decimal], index: int, window: int) -> Optional[Decimal]:
    """Average of `window` prices ending at `index` (inclusive), oldest-first list.

    Returns None if there aren't enough prior prices to fill the window.
    """
    if index + 1 < window:
        return None
    window_slice = prices[index + 1 - window : index + 1]
    return sum(window_slice) / Decimal(window)


def pct_change(prices: list[Decimal], index: int) -> Optional[Decimal]:
    """% change vs. the previous price in an oldest-first list. None for the first row."""
    if index == 0:
        return None
    previous = prices[index - 1]
    if previous == 0:
        return None
    return ((prices[index] - previous) / previous) * Decimal(100)


def build_commodity_section(
    symbol: str,
    name: str,
    snapshots_oldest_first: list[tuple[date, Decimal]],
    alert_snapshot_ids: set[int],
    snapshot_ids_oldest_first: list[int],
) -> CommodityReportSection:
    """Build one commodity's report rows from its snapshots in the date range.

    BUSINESS RULE (FR-4.3): if fewer than MIN_SNAPSHOTS_FOR_AVERAGES snapshots
    are in range, the commodity is still included with raw prices only (no
    moving averages), and `excluded_note` records why.
    """
    section = CommodityReportSection(symbol=symbol, name=name)

    if not snapshots_oldest_first:
        section.excluded_note = "No price snapshots in the selected date range."
        return section

    prices = [price for _, price in snapshots_oldest_first]
    has_enough_for_averages = len(prices) >= MIN_SNAPSHOTS_FOR_AVERAGES

    if not has_enough_for_averages:
        section.excluded_note = (
            f"Only {len(prices)} snapshot(s) in range "
            f"(need {MIN_SNAPSHOTS_FOR_AVERAGES} for moving averages) — "
            "showing raw prices only."
        )

    for i, (captured_at, price) in enumerate(snapshots_oldest_first):
        snapshot_id = snapshot_ids_oldest_first[i]
        section.rows.append(
            PriceRow(
                captured_at=captured_at,
                price=price,
                ma_5=moving_average(prices, i, 5) if has_enough_for_averages else None,
                ma_10=moving_average(prices, i, 10) if has_enough_for_averages else None,
                pct_change=pct_change(prices, i),
                is_alert=snapshot_id in alert_snapshot_ids,
            )
        )

    return section


def _report_file_path(filename: str) -> Path:
    return REPORTS_DIR / filename


def _build_workbook(
    trader_name: str,
    date_from: date,
    date_to: date,
    sections: list[CommodityReportSection],
    excluded: list[dict],
) -> Workbook:
    wb = Workbook()
    summary = wb.active
    summary.title = "Summary"
    summary.append(["Trader", trader_name])
    summary.append(["Report Date From", date_from.isoformat()])
    summary.append(["Report Date To", date_to.isoformat()])
    summary.append(["Generated At", datetime.now(timezone.utc).isoformat()])
    summary.append([])
    summary.append(["Included Commodities"])
    summary.append(["Symbol", "Name", "Rows", "Notes"])
    for section in sections:
        summary.append(
            [
                section.symbol,
                section.name,
                len(section.rows),
                section.excluded_note or "",
            ]
        )
    summary.append([])
    summary.append(["Excluded Commodities"])
    summary.append(["Symbol", "Name", "Reason"])
    for excluded_item in excluded:
        summary.append(
            [excluded_item["symbol"], excluded_item["name"], excluded_item["reason"]]
        )

    for section in sections:
        worksheet = wb.create_sheet(title=section.symbol[:31])
        worksheet.append(["Captured At", "Price", "MA 5", "MA 10", "% Change", "Is Alert"])
        for row in section.rows:
            worksheet.append(
                [
                    row.captured_at.isoformat(),
                    float(row.price),
                    float(row.ma_5) if row.ma_5 is not None else None,
                    float(row.ma_10) if row.ma_10 is not None else None,
                    float(round(row.pct_change, 2)) if row.pct_change is not None else None,
                    "YES" if row.is_alert else "NO",
                ]
            )

    return wb


@router.post("/", response_model=ReportOut, status_code=201)
def create_report(
    payload: ReportCreate,
    db: Session = Depends(get_db),
    acting_trader=Depends(get_current_trader),
):
    if not acting_trader.active:
        raise HTTPException(status_code=401, detail="Inactive trader")

    watchlist_items = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.trader_id == acting_trader.id)
        .all()
    )
    if not watchlist_items:
        raise HTTPException(status_code=400, detail="add a commodity to your watchlist first")

    commodity_ids = [item.commodity_id for item in watchlist_items]
    commodities = (
        db.query(Commodity)
        .filter(Commodity.id.in_(commodity_ids))
        .order_by(Commodity.symbol)
        .all()
    )

    start_dt = datetime.combine(payload.date_from, time.min)
    end_dt = datetime.combine(payload.date_to, time.max)

    sections: list[CommodityReportSection] = []
    excluded: list[dict] = []

    for commodity in commodities:
        snapshots = (
            db.query(PriceSnapshot)
            .filter(
                PriceSnapshot.commodity_id == commodity.id,
                PriceSnapshot.captured_at >= start_dt,
                PriceSnapshot.captured_at <= end_dt,
            )
            .order_by(PriceSnapshot.captured_at.asc())
            .all()
        )

        snapshot_ids = [snapshot.id for snapshot in snapshots]
        alert_snapshot_ids = {
            alert.price_snapshot_id
            for alert in db.query(PriceAlert)
            .filter(PriceAlert.price_snapshot_id.in_(snapshot_ids))
            .all()
        }

        section = build_commodity_section(
            symbol=commodity.symbol,
            name=commodity.name,
            snapshots_oldest_first=[(snapshot.captured_at.date(), snapshot.price) for snapshot in snapshots],
            alert_snapshot_ids=alert_snapshot_ids,
            snapshot_ids_oldest_first=snapshot_ids,
        )
        sections.append(section)

        if not section.rows:
            excluded.append(
                {
                    "symbol": commodity.symbol,
                    "name": commodity.name,
                    "reason": section.excluded_note or "No price snapshots in the selected date range.",
                }
            )

    filename = f"commodity_report_{acting_trader.id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}.xlsx"
    workbook = _build_workbook(
        trader_name=acting_trader.name,
        date_from=payload.date_from,
        date_to=payload.date_to,
        sections=sections,
        excluded=excluded,
    )
    filepath = _report_file_path(filename)
    workbook.save(filepath)

    report = Report(
        trader_id=acting_trader.id,
        date_from=payload.date_from,
        date_to=payload.date_to,
        filename=filename,
        row_count=sum(len(section.rows) for section in sections),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


# GET /reports
# List reports owned by the acting trader, paginated.
@router.get("/", response_model=list[ReportOut])
def list_reports(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    acting_trader=Depends(get_current_trader),
):
    return (
        db.query(Report)
        .filter(Report.trader_id == acting_trader.id)
        .order_by(Report.generated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# GET /reports/{report_id}
# Return metadata for one report, scoped to the acting trader.
@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    acting_trader=Depends(get_current_trader),
):
    report = db.get(Report, report_id)
    if report is None or report.trader_id != acting_trader.id:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/download")
def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    acting_trader=Depends(get_current_trader),
):
    if not acting_trader.active:
        raise HTTPException(status_code=401, detail="Inactive trader")

    report = db.get(Report, report_id)
    if report is None or report.trader_id != acting_trader.id:
        raise HTTPException(status_code=404, detail="Report not found")

    path = _report_file_path(report.filename)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")

    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=report.filename,
    )
