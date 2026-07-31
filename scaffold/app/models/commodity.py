from app.database import Base

# ─────────────────────────────────────────────────────────────────────────────
# TODO: Define the `commodities` table (seeded, read-only reference table).
#
# Columns:
#   id          — Integer, primary key
#   symbol      — String(10), not null, unique
#   name        — String(100), not null
#   unit        — String(20), not null
#   desk        — Enum("metals", "energy", "agriculture"), not null
#   is_active   — Boolean, not null, default True
#
# Also add:
#   price_snapshots = relationship("PriceSnapshot", back_populates="commodity")
#   watchlist_items = relationship("WatchlistItem", back_populates="commodity")
#   price_alerts = relationship("PriceAlert", back_populates="commodity")
# ─────────────────────────────────────────────────────────────────────────────


class Commodity(Base):
    __tablename__ = "commodities"

    # TODO: columns and relationships go here
    pass
