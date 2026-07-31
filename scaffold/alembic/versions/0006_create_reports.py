"""create reports table

Revision ID: 0006
Revises: 0005
Create Date: 2024-01-01 00:00:06

"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("trader_id", sa.Integer, sa.ForeignKey("traders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date_from", sa.Date, nullable=False),
        sa.Column("date_to", sa.Date, nullable=False),
        sa.Column("filename", sa.String(200), nullable=False),
        sa.Column("row_count", sa.Integer, nullable=False),
        sa.Column("generated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("reports")
