from app.database import Base

# ─────────────────────────────────────────────────────────────────────────────
# TODO: Define the `reports` table.
#
# Columns:
#   id            — Integer, primary key
#   trader_id     — Integer, ForeignKey("traders.id"), not null
#   date_from     — Date, not null
#   date_to       — Date, not null
#   filename      — String(200), not null
#   row_count     — Integer, not null
#   generated_at  — DateTime, not null, server default now()
#
# Also add:
#   trader = relationship("Trader", back_populates="reports")
# ─────────────────────────────────────────────────────────────────────────────


class Report(Base):
    __tablename__ = "reports"

    # TODO: columns and relationships go here
    pass
