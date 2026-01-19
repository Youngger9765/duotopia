"""Fix incorrect revision ID in alembic_version table

This migration fixes the alembic_version table to point to the correct revision ID.
The previous migration used an invalid revision ID '7f8g9h0i1j2k' which contained
non-hexadecimal characters.

Revision ID: 9a8b7c6d5e4f
Revises: 7f8g9h0i1j2k
Create Date: 2026-01-19 14:01:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "9a8b7c6d5e4f"
down_revision = "7f8g9h0i1j2k"  # Point to the invalid revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    This migration does nothing. It's a transition step.

    Alembic automatically updates alembic_version table when
    running migrations. We don't need to do it manually.
    """

    pass


def downgrade() -> None:
    """
    This migration does nothing.
    """

    pass
