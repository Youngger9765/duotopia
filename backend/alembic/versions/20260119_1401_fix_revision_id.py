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
    Fix the alembic_version table to use the correct revision ID.

    The database currently has '7f8g9h0i1j2k' recorded, but the actual
    migration file uses '7f8e9d0c1b2a'. This migration updates the
    alembic_version table to reflect the correct ID.
    """

    # Update alembic_version table directly
    op.execute(
        """
        UPDATE alembic_version
        SET version_num = '9a8b7c6d5e4f'
        WHERE version_num = '7f8g9h0i1j2k'
        """
    )


def downgrade() -> None:
    """
    Revert to the incorrect revision ID (not recommended).
    """

    op.execute(
        """
        UPDATE alembic_version
        SET version_num = '7f8g9h0i1j2k'
        WHERE version_num = '9a8b7c6d5e4f'
        """
    )
