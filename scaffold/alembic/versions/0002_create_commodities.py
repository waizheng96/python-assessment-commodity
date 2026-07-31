"""create commodities table

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-01 00:00:02

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

desk_enum = sa.Enum("metals", "energy", "agriculture", name="desk_enum")


def upgrade() -> None:
    op.create_table(
        "commodities",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(10), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("desk", desk_enum, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_table("commodities")
