"""add admin features: is_admin and admin_metadata

Revision ID: 59686379aa20
Revises: 15aeb16a5c92
Create Date: 2025-11-15 22:16:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "59686379aa20"
down_revision: Union[str, None] = "5cff70f7dc07"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_admin column to teachers table
    op.add_column(
        "teachers",
        sa.Column(
            "is_admin", sa.Boolean(), nullable=True, server_default=sa.text("false")
        ),
    )

    # Add admin operation tracking columns to subscription_periods
    op.add_column(
        "subscription_periods", sa.Column("admin_id", sa.Integer(), nullable=True)
    )
    op.add_column(
        "subscription_periods", sa.Column("admin_reason", sa.Text(), nullable=True)
    )
    op.add_column(
        "subscription_periods",
        sa.Column(
            "admin_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )

    # Add foreign key constraint for admin_id
    op.create_foreign_key(
        "fk_subscription_periods_admin_id",
        "subscription_periods",
        "teachers",
        ["admin_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Remove foreign key constraint
    op.drop_constraint(
        "fk_subscription_periods_admin_id", "subscription_periods", type_="foreignkey"
    )

    # Remove admin operation tracking columns
    op.drop_column("subscription_periods", "admin_metadata")
    op.drop_column("subscription_periods", "admin_reason")
    op.drop_column("subscription_periods", "admin_id")

    # Remove is_admin column
    op.drop_column("teachers", "is_admin")
