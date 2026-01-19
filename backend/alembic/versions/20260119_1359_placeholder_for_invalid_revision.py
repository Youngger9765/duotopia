"""Placeholder for invalid revision ID

This is a placeholder migration that does nothing.
It exists only to allow Alembic to locate the invalid revision ID
that was accidentally deployed to preview database.

Revision ID: 7f8g9h0i1j2k
Revises: 04221a3e73fc
Create Date: 2026-01-19 13:59:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "7f8g9h0i1j2k"  # The invalid ID that exists in database
down_revision = "04221a3e73fc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    This migration does nothing.
    It's a placeholder to allow Alembic to find the invalid revision ID.
    """
    pass


def downgrade() -> None:
    """
    This migration does nothing.
    """
    pass
