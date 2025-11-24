"""add_sentence_making_to_contenttype_enum

Revision ID: 1016469bbf26
Revises: 85160fa3d3cc
Create Date: 2025-11-10 13:54:29.382598

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1016469bbf26"
down_revision: Union[str, None] = "85160fa3d3cc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add SENTENCE_MAKING to contenttype enum
    # Check if value already exists to support shared database environments (develop/staging)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumlabel = 'SENTENCE_MAKING'
                AND enumtypid = (
                    SELECT oid FROM pg_type WHERE typname = 'contenttype'
                )
            ) THEN
                ALTER TYPE contenttype ADD VALUE 'SENTENCE_MAKING';
            END IF;
        END
        $$;
    """
    )


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values easily
    # This would require recreating the enum type
    pass
