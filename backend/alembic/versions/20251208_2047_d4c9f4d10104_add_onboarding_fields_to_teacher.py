"""add_onboarding_fields_to_teacher

Revision ID: d4c9f4d10104
Revises: 288ad5a75206
Create Date: 2025-12-08 20:47:28.616300

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4c9f4d10104'
down_revision: Union[str, None] = '288ad5a75206'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add onboarding tracking fields to teachers table
    # Issue #61: New user onboarding automation
    op.add_column(
        "teachers",
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "teachers",
        sa.Column("onboarding_started_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    # Remove onboarding tracking fields from teachers table
    op.drop_column("teachers", "onboarding_started_at")
    op.drop_column("teachers", "onboarding_completed")
