from app.database import Base

# ─────────────────────────────────────────────────────────────────────────────
# TODO: Define the `traders` table.
#
# Columns:
#   id          — Integer, primary key
#   name        — String(100), not null
#   email       — String(150), not null, unique
#   desk        — Enum("metals", "energy", "agriculture"), not null
#   active      — Boolean, not null, default True
#   created_at  — DateTime, not null, server default now()
#
# Also add:
#   watchlist_items = relationship("WatchlistItem", back_populates="trader")
#   reports = relationship("Report", back_populates="trader")
# ─────────────────────────────────────────────────────────────────────────────


class Trader(Base):
    __tablename__ = "traders"

    # TODO: columns and relationships go here
    pass
