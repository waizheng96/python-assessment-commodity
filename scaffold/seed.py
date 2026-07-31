"""
Seed data for Commodity Watch — complete and realistic. Do NOT modify this file.

Uses SQLAlchemy Core against the tables created by Alembic migrations, so it
runs correctly before you've written a single line in app/models/.

Run after `alembic upgrade head`:
    python seed.py
"""
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from sqlalchemy import MetaData, create_engine, insert

load_dotenv()

THRESHOLDS = {"metals": 1.5, "energy": 3.0, "agriculture": 1.5}

engine = create_engine(os.environ["DATABASE_URL"])
metadata = MetaData()
metadata.reflect(bind=engine)

traders = metadata.tables["traders"]
commodities = metadata.tables["commodities"]
price_snapshots = metadata.tables["price_snapshots"]
watchlist_items = metadata.tables["watchlist_items"]
price_alerts = metadata.tables["price_alerts"]
reports = metadata.tables["reports"]

COMMODITY_DEFS = [
    ("XAU", "Gold", "oz", "metals"),
    ("XAG", "Silver", "oz", "metals"),
    ("WTI", "Crude Oil", "barrel", "energy"),
    ("NG", "Natural Gas", "mmbtu", "energy"),
    ("COFFEE", "Coffee", "lb", "agriculture"),
]

PRICE_SERIES = {
    "XAU": [1950, 1955, 1948, 1960, 1990, 1985, 1978, 1982, 1990, 1995],       # day5 jump: +1.53%
    "XAG": [24.0, 24.1, 23.9, 24.2, 24.60, 24.55, 24.5, 24.6, 24.65, 24.7],     # day5 jump: +1.65%
    "WTI": [78.0, 78.5, 77.8, 79.0, 81.5, 81.0, 80.5, 81.2, 81.8, 82.0],        # day5 jump: +3.16%
    "NG": [2.50, 2.52, 2.48, 2.55, 2.60, 2.65, 2.58, 2.62, 2.70, 2.75],         # day9 jump: +3.05%
    "COFFEE": [1.85, 1.87, 1.84, 1.89, 1.92, 1.95, 1.93, 1.96, 1.98, 2.00],     # day6 jump: +1.56%
}

WATCHLIST = {
    "Faizal Rahman": ["XAU", "XAG"],
    "Chen Wei Ling": ["WTI", "NG"],
    "Kumar Selvarajan": ["COFFEE"],
}


def main():
    with engine.begin() as conn:
        conn.execute(reports.delete())
        conn.execute(price_alerts.delete())
        conn.execute(watchlist_items.delete())
        conn.execute(price_snapshots.delete())
        conn.execute(commodities.delete())
        conn.execute(traders.delete())

        # ── Traders — covers all 3 desks + one inactive account ─────────────
        trader_rows = conn.execute(
            insert(traders).returning(traders.c.id, traders.c.name),
            [
                {"name": "Faizal Rahman", "email": "faizal.rahman@orepoint.com", "desk": "metals", "active": True},
                {"name": "Chen Wei Ling", "email": "wei.ling.chen@orepoint.com", "desk": "energy", "active": True},
                {"name": "Kumar Selvarajan", "email": "kumar.selvarajan@orepoint.com", "desk": "agriculture", "active": True},
                {"name": "Aisyah Zainal", "email": "aisyah.zainal@orepoint.com", "desk": "metals", "active": False},
            ],
        ).fetchall()
        trader_ids = {row.name: row.id for row in trader_rows}

        # ── Commodities (reference table) ───────────────────────────────────
        commodity_rows = conn.execute(
            insert(commodities).returning(commodities.c.id, commodities.c.symbol, commodities.c.desk),
            [
                {"symbol": symbol, "name": name, "unit": unit, "desk": desk, "is_active": True}
                for (symbol, name, unit, desk) in COMMODITY_DEFS
            ],
        ).fetchall()
        commodity_ids = {row.symbol: row.id for row in commodity_rows}
        commodity_desk = {row.symbol: row.desk for row in commodity_rows}

        # ── Price snapshots + auto-generated desk-threshold alerts ──────────
        start_date = datetime.utcnow() - timedelta(days=10)
        alert_count = 0

        for symbol, prices in PRICE_SERIES.items():
            commodity_id = commodity_ids[symbol]
            threshold = THRESHOLDS[commodity_desk[symbol]]
            prev_price = None

            for day_offset, price in enumerate(prices):
                captured_at = start_date + timedelta(days=day_offset)
                snapshot_id = conn.execute(
                    insert(price_snapshots).returning(price_snapshots.c.id),
                    [{"commodity_id": commodity_id, "price": price, "captured_at": captured_at, "source": "seed"}],
                ).scalar_one()

                if prev_price is not None:
                    pct_change = round((price - prev_price) / prev_price * 100, 2)
                    if abs(pct_change) > threshold:
                        conn.execute(
                            insert(price_alerts),
                            [{
                                "commodity_id": commodity_id,
                                "price_snapshot_id": snapshot_id,
                                "pct_change": pct_change,
                                "threshold_used": threshold,
                                "threshold_breached": True,
                                "created_at": captured_at,
                            }],
                        )
                        alert_count += 1

                prev_price = price

        # ── Watchlists — supports the per-trader isolation test ─────────────
        for trader_name, symbols in WATCHLIST.items():
            conn.execute(
                insert(watchlist_items),
                [{"trader_id": trader_ids[trader_name], "commodity_id": commodity_ids[s], "added_at": datetime.utcnow()} for s in symbols],
            )

        # ── One sample report row (metadata only) ────────────────────────────
        conn.execute(
            insert(reports),
            [{
                "trader_id": trader_ids["Faizal Rahman"],
                "date_from": start_date.date(),
                "date_to": (start_date + timedelta(days=9)).date(),
                "filename": "commodity_report_sample.xlsx",
                "row_count": 20,
                "generated_at": datetime.utcnow(),
            }],
        )

    print(f"Seeded {len(trader_ids)} traders, {len(commodity_ids)} commodities, "
          f"{len(PRICE_SERIES) * 10} price snapshots, {alert_count} alerts, "
          f"{sum(len(v) for v in WATCHLIST.values())} watchlist entries, 1 report.")


if __name__ == "__main__":
    main()
