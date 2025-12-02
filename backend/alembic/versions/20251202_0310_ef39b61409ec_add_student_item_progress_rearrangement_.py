"""add_student_item_progress_rearrangement_fields

Add rearrangement activity fields to student_item_progress table:
- error_count: number of wrong selections
- correct_word_count: number of correctly selected words
- retry_count: number of times student chose to retry
- expected_score: current expected score during answering
- timeout_ended: whether the question ended due to timeout

Revision ID: ef39b61409ec
Revises: 3ee73ce1da44
Create Date: 2025-12-02 03:10:55.421561

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef39b61409ec'
down_revision: Union[str, None] = '3ee73ce1da44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add error_count: number of wrong selections
    op.execute("""
        ALTER TABLE student_item_progress
        ADD COLUMN IF NOT EXISTS error_count INTEGER DEFAULT 0;
    """)

    # Add correct_word_count: number of correctly selected words
    op.execute("""
        ALTER TABLE student_item_progress
        ADD COLUMN IF NOT EXISTS correct_word_count INTEGER DEFAULT 0;
    """)

    # Add retry_count: number of times student chose to retry
    op.execute("""
        ALTER TABLE student_item_progress
        ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;
    """)

    # Add expected_score: current expected score during answering
    op.execute("""
        ALTER TABLE student_item_progress
        ADD COLUMN IF NOT EXISTS expected_score DECIMAL(5,2) DEFAULT 0;
    """)

    # Add timeout_ended: whether the question ended due to timeout
    op.execute("""
        ALTER TABLE student_item_progress
        ADD COLUMN IF NOT EXISTS timeout_ended BOOLEAN DEFAULT FALSE;
    """)

    # Add rearrangement_data: JSON field to store word selection history
    op.execute("""
        ALTER TABLE student_item_progress
        ADD COLUMN IF NOT EXISTS rearrangement_data JSONB DEFAULT NULL;
    """)


def downgrade() -> None:
    # Following additive migration principle, not removing columns
    pass
