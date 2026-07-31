"""create traders table

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

desk_enum = PGEnum("metals", "energy", "agriculture", name="desk_enum", create_type=False)


def upgrade() -> None:
    desk_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "traders",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(150), nullable=False, unique=True),
        sa.Column("desk", desk_enum, nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("traders")
    desk_enum.drop(op.get_bind(), checkfirst=True)
