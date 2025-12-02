"""add_content_item_word_count

Add word_count and max_errors columns to content_items table:
- word_count: number of words in the sentence (auto-calculated)
- max_errors: allowed error count based on word_count
  - 2-10 words: 3 errors allowed
  - 11-25 words: 5 errors allowed

Revision ID: 3ee73ce1da44
Revises: e263ed443762
Create Date: 2025-12-02 03:09:56.086232

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ee73ce1da44'
down_revision: Union[str, None] = 'e263ed443762'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add word_count column to content_items
    op.execute("""
        ALTER TABLE content_items
        ADD COLUMN IF NOT EXISTS word_count INTEGER DEFAULT NULL;
    """)

    # Add max_errors column to content_items
    op.execute("""
        ALTER TABLE content_items
        ADD COLUMN IF NOT EXISTS max_errors INTEGER DEFAULT NULL;
    """)

    # Calculate word_count for existing content_items
    # Using array_length with string_to_array to count words
    op.execute("""
        UPDATE content_items
        SET word_count = array_length(
            string_to_array(trim(regexp_replace(text, '\\s+', ' ', 'g')), ' '),
            1
        )
        WHERE word_count IS NULL AND text IS NOT NULL AND text != '';
    """)

    # Calculate max_errors based on word_count
    # 2-10 words: 3 errors, 11-25 words: 5 errors
    op.execute("""
        UPDATE content_items
        SET max_errors = CASE
            WHEN word_count IS NULL THEN NULL
            WHEN word_count <= 10 THEN 3
            ELSE 5
        END
        WHERE max_errors IS NULL;
    """)


def downgrade() -> None:
    # Following additive migration principle, not removing columns
    pass
