from app.database import Base

# ─────────────────────────────────────────────────────────────────────────────
# TODO: Define the `watchlist_items` table (junction table — the domain-unique
# scoping concept for this assessment: each trader's watchlist is isolated
# from every other trader's).
#
# Columns:
#   id             — Integer, primary key
#   trader_id      — Integer, ForeignKey("traders.id"), not null
#   commodity_id   — Integer, ForeignKey("commodities.id"), not null
#   added_at       — DateTime, not null, server default now()
#   UniqueConstraint(trader_id, commodity_id)
#
# Also add:
#   trader = relationship("Trader", back_populates="watchlist_items")
#   commodity = relationship("Commodity", back_populates="watchlist_items")
#
# BUSINESS RULE (enforced in the router, not here): GET /watchlist must only
# ever return the requesting trader's own rows — never another trader's.
# ─────────────────────────────────────────────────────────────────────────────


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    # TODO: columns and relationships go here
    pass
