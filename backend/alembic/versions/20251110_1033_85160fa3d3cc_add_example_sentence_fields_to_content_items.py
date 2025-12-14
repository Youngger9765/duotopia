"""add example sentence fields to content_items

Revision ID: 85160fa3d3cc
Revises: 59686379aa20
Create Date: 2025-11-10 10:33:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "85160fa3d3cc"
down_revision: Union[str, None] = "59686379aa20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add example sentence fields to content_items table
    # Use IF NOT EXISTS to support shared database environments (develop/staging)
    op.execute(
        """
        ALTER TABLE content_items
        ADD COLUMN IF NOT EXISTS example_sentence TEXT
    """
    )
    op.execute(
        """
        ALTER TABLE content_items
        ADD COLUMN IF NOT EXISTS example_sentence_translation TEXT
    """
    )
    op.execute(
        """
        ALTER TABLE content_items
        ADD COLUMN IF NOT EXISTS example_sentence_definition TEXT
    """
    )


def downgrade() -> None:
    # Remove example sentence fields from content_items table
    op.drop_column("content_items", "example_sentence_definition")
    op.drop_column("content_items", "example_sentence_translation")
    op.drop_column("content_items", "example_sentence")
