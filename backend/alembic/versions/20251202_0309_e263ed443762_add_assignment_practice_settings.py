"""add_assignment_practice_settings

Add new columns to assignments table for practice mode settings:
- practice_mode: 'reading' (例句朗讀) / 'rearrangement' (例句重組)
- time_limit_per_question: 10/20/30/40 seconds per question
- shuffle_questions: whether to shuffle question order
- play_audio: whether to play audio (rearrangement mode only)
- score_category: 'speaking' / 'listening' / 'writing'

Revision ID: e263ed443762
Revises: 8ccd904efbd3
Create Date: 2025-12-02 03:09:06.566696

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e263ed443762'
down_revision: Union[str, None] = '8ccd904efbd3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add practice mode settings to assignments table
    # Using IF NOT EXISTS pattern for shared database environments

    # practice_mode: 'reading' (例句朗讀) / 'rearrangement' (例句重組)
    op.execute("""
        ALTER TABLE assignments
        ADD COLUMN IF NOT EXISTS practice_mode VARCHAR(20) DEFAULT 'reading';
    """)

    # time_limit_per_question: seconds per question (10/20/30/40)
    op.execute("""
        ALTER TABLE assignments
        ADD COLUMN IF NOT EXISTS time_limit_per_question INTEGER DEFAULT 40;
    """)

    # shuffle_questions: whether to shuffle question order
    op.execute("""
        ALTER TABLE assignments
        ADD COLUMN IF NOT EXISTS shuffle_questions BOOLEAN DEFAULT FALSE;
    """)

    # play_audio: whether to play audio (for rearrangement mode)
    op.execute("""
        ALTER TABLE assignments
        ADD COLUMN IF NOT EXISTS play_audio BOOLEAN DEFAULT FALSE;
    """)

    # score_category: 'speaking' / 'listening' / 'writing'
    op.execute("""
        ALTER TABLE assignments
        ADD COLUMN IF NOT EXISTS score_category VARCHAR(20) DEFAULT NULL;
    """)

    # Set default score_category for existing assignments based on content type
    # Existing READING_ASSESSMENT assignments should be 'speaking'
    # Note: Only use existing enum values here (READING_ASSESSMENT)
    # New values (EXAMPLE_SENTENCES) will be handled in later migrations
    op.execute("""
        UPDATE assignments a
        SET
            practice_mode = 'reading',
            score_category = 'speaking'
        WHERE a.practice_mode IS NULL
        AND EXISTS (
            SELECT 1 FROM assignment_contents ac
            JOIN contents c ON c.id = ac.content_id
            WHERE ac.assignment_id = a.id
            AND c.type = 'READING_ASSESSMENT'
        );
    """)


def downgrade() -> None:
    # Following additive migration principle, not removing columns
    pass
