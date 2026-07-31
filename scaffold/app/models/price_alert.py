from app.database import Base

# ─────────────────────────────────────────────────────────────────────────────
# TODO: Define the `price_alerts` table.
#
# Columns:
#   id                  — Integer, primary key
#   commodity_id        — Integer, ForeignKey("commodities.id"), not null
#   price_snapshot_id   — Integer, ForeignKey("price_snapshots.id"), not null, unique
#   pct_change          — Numeric(6, 2), not null
#   threshold_used      — Numeric(4, 2), not null — records which threshold
#                          (1.5 for metals/agriculture, 3.0 for energy) was applied
#   threshold_breached  — Boolean, not null
#   created_at          — DateTime, not null, server default now()
#
# Also add:
#   commodity = relationship("Commodity", back_populates="price_alerts")
#   price_snapshot = relationship("PriceSnapshot", back_populates="alert")
#
# BUSINESS RULE (enforced in the router, not here): the threshold applied
# must be looked up from the commodity's desk — 1.5% for metals/agriculture,
# 3.0% for energy — never hardcoded to a single value for all commodities.
# ─────────────────────────────────────────────────────────────────────────────


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    # TODO: columns and relationships go here
    pass
