from datetime import datetime

from fastapi import FastAPI

from app.error_handlers import register_error_handlers
from app.routers import traders, commodities, watchlist, alerts, reports

app = FastAPI(title="Commodity Watch API")

register_error_handlers(app)

app.include_router(traders.router, prefix="/traders", tags=["traders"])
app.include_router(commodities.router, prefix="/commodities", tags=["commodities"])
app.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
