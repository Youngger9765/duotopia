"""add_email_verification_fields

Revision ID: f66a09eba7e7
Revises: 47e26e8bf64b
Create Date: 2025-09-07 22:51:59.463819

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "f66a09eba7e7"
down_revision: Union[str, None] = "47e26e8bf64b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No-op migration - all required changes were already applied in previous migrations
    # The email verification fields were added in migration 47e26e8bf64b
    # All tables and schema are already in place
    pass


def downgrade() -> None:
    # SAFE: No-op downgrade - this migration doesn't change anything
    # This migration is a placeholder and doesn't modify the database schema
    pass
