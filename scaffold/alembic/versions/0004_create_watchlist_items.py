"""create watchlist_items table

Revision ID: 0004
Revises: 0003
Create Date: 2024-01-01 00:00:04

"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("trader_id", sa.Integer, sa.ForeignKey("traders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("commodity_id", sa.Integer, sa.ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("added_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("trader_id", "commodity_id", name="uq_watchlist_trader_commodity"),
    )


def downgrade() -> None:
    op.drop_table("watchlist_items")
