from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    commodity_id: Mapped[int] = mapped_column(
        ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False
    )
    price_snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("price_snapshots.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    pct_change: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    threshold_used: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    threshold_breached: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    commodity = relationship("Commodity", back_populates="price_alerts")
    price_snapshot = relationship("PriceSnapshot", back_populates="alert")