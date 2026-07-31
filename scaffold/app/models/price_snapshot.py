from app.database import Base

# ─────────────────────────────────────────────────────────────────────────────
# TODO: Define the `price_snapshots` table.
#
# Columns:
#   id             — Integer, primary key
#   commodity_id   — Integer, ForeignKey("commodities.id"), not null
#   price          — Numeric(12, 4), not null
#   captured_at    — DateTime, not null
#   source         — String(100), not null
#
# Also add:
#   commodity = relationship("Commodity", back_populates="price_snapshots")
#   alert = relationship("PriceAlert", back_populates="price_snapshot", uselist=False)
#
# BUSINESS RULE (enforced in the router, not here): a new snapshot's
# captured_at must be later than the commodity's most recent existing snapshot.
# ─────────────────────────────────────────────────────────────────────────────


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    # TODO: columns and relationships go here
    pass
