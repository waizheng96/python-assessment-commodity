"""create price_alerts table

Revision ID: 0005
Revises: 0004
Create Date: 2024-01-01 00:00:05

"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "price_alerts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("commodity_id", sa.Integer, sa.ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("price_snapshot_id", sa.Integer, sa.ForeignKey("price_snapshots.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("pct_change", sa.Numeric(6, 2), nullable=False),
        sa.Column("threshold_used", sa.Numeric(4, 2), nullable=False),
        sa.Column("threshold_breached", sa.Boolean, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("price_alerts")
