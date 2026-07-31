from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.trader import Trader


def get_current_trader(
    x_trader_id: int = Header(..., description="Login-As simulation — the acting trader's id"),
    db: Session = Depends(get_db),
) -> Trader:
    """Fully wired — do not modify.

    Resolves the X-Trader-Id header to a Trader row. Whether that trader is
    allowed to perform the specific action being requested is a BUSINESS RULE
    and is checked inside the route handler, not here.
    """
    trader = db.get(Trader, x_trader_id)
    if trader is None:
        raise HTTPException(status_code=401, detail="Unknown X-Trader-Id")
    return trader
