# ─────────────────────────────────────────────────────────────────────────────
# Import every model module here so Base.metadata sees every table when
# Alembic autogenerates, and so `from app.models import Trader` works.
#
# TODO: Once you complete each model file below, also add the SQLAlchemy
# `relationship()` calls described here (the relationship() call itself goes
# INSIDE each model class in its own file — this list is just the checklist):
#
#   Trader.watchlist_items      -> one Trader has many WatchlistItem
#   Trader.reports              -> one Trader has many Report
#   Commodity.price_snapshots   -> one Commodity has many PriceSnapshot
#   Commodity.watchlist_items   -> one Commodity has many WatchlistItem
#   Commodity.price_alerts      -> one Commodity has many PriceAlert
#   PriceSnapshot.commodity     -> many PriceSnapshot belong to one Commodity
#   PriceSnapshot.alert         -> one PriceSnapshot has one PriceAlert (uselist=False)
#   WatchlistItem.trader        -> many WatchlistItem belong to one Trader
#   WatchlistItem.commodity     -> many WatchlistItem belong to one Commodity
#   PriceAlert.commodity        -> many PriceAlert belong to one Commodity
#   PriceAlert.price_snapshot   -> many PriceAlert belong to one PriceSnapshot
#   Report.trader                -> many Report belong to one Trader
# ─────────────────────────────────────────────────────────────────────────────

from app.models.trader import Trader  # noqa: F401
from app.models.commodity import Commodity  # noqa: F401
from app.models.price_snapshot import PriceSnapshot  # noqa: F401
from app.models.watchlist_item import WatchlistItem  # noqa: F401
from app.models.price_alert import PriceAlert  # noqa: F401
from app.models.report import Report  # noqa: F401
