from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from app.models._enums import DeskEnum


class Commodity(Base):
    __tablename__ = "commodities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    desk: Mapped[str] = mapped_column(DeskEnum, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    price_snapshots = relationship(
        "PriceSnapshot", back_populates="commodity", cascade="all, delete-orphan"
    )
    watchlist_items = relationship(
        "WatchlistItem", back_populates="commodity", cascade="all, delete-orphan"
    )
    price_alerts = relationship(
        "PriceAlert", back_populates="commodity", cascade="all, delete-orphan"
    )