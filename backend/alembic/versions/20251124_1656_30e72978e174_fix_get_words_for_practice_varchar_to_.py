"""fix get_words_for_practice varchar to text type mismatch

Revision ID: 30e72978e174
Revises: 59686379aa20
Create Date: 2025-11-24 16:56:32.680383

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "30e72978e174"
down_revision: Union[str, None] = "59686379aa20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fix type mismatch: change text VARCHAR to text TEXT and translation VARCHAR to TEXT
    # The content_items.text and content_items.translation columns are TEXT type, not VARCHAR

    # Drop the function first (required for changing return types)
    op.execute("DROP FUNCTION IF EXISTS get_words_for_practice(INTEGER, INTEGER)")

    # Recreate with correct types
    op.execute(
        """
        CREATE FUNCTION get_words_for_practice(
            p_student_assignment_id INTEGER,
            p_limit_count INTEGER DEFAULT 10
        ) RETURNS TABLE (
            content_item_id INTEGER,
            text TEXT,
            translation TEXT,
            example_sentence TEXT,
            example_sentence_translation TEXT,
            audio_url TEXT,
            memory_strength DECIMAL,
            priority_score DECIMAL
        ) AS $$
        BEGIN
            RETURN QUERY
            WITH assignment_contents AS (
                -- Get all content_items for this assignment
                SELECT DISTINCT ci.id as content_item_id
                FROM student_assignments sa
                JOIN student_content_progress scp ON scp.student_assignment_id = sa.id
                JOIN content_items ci ON ci.content_id = scp.content_id
                WHERE sa.id = p_student_assignment_id
            )
            SELECT
                ci.id,
                ci.text,
                ci.translation,
                ci.example_sentence,
                ci.example_sentence_translation,
                ci.audio_url,
                COALESCE(uwp.memory_strength, 0) as memory_strength,
                -- Priority calculation:
                -- 1. Never practiced (priority = 100)
                -- 2. Due for review + low memory (priority = 50-100)
                -- 3. Not due but low memory (priority = 0-30)
                CASE
                    WHEN uwp.id IS NULL THEN 100  -- Never practiced
                    WHEN uwp.next_review_at IS NULL THEN 100
                    WHEN uwp.next_review_at <= NOW() THEN
                        50 + (1 - uwp.memory_strength) * 50
                    ELSE
                        (1 - uwp.memory_strength) * 30
                END as priority_score
            FROM assignment_contents ac
            JOIN content_items ci ON ci.id = ac.content_item_id
            LEFT JOIN user_word_progress uwp ON
                uwp.student_assignment_id = p_student_assignment_id AND
                uwp.content_item_id = ci.id
            ORDER BY priority_score DESC, RANDOM()
            LIMIT p_limit_count;
        END;
        $$ LANGUAGE plpgsql;
    """
    )


def downgrade() -> None:
    # Revert to original version with VARCHAR
    # Drop the function first (required for changing return types)
    op.execute("DROP FUNCTION IF EXISTS get_words_for_practice(INTEGER, INTEGER)")

    # Recreate with original VARCHAR types
    op.execute(
        """
        CREATE FUNCTION get_words_for_practice(
            p_student_assignment_id INTEGER,
            p_limit_count INTEGER DEFAULT 10
        ) RETURNS TABLE (
            content_item_id INTEGER,
            text VARCHAR,
            translation VARCHAR,
            example_sentence TEXT,
            example_sentence_translation TEXT,
            audio_url TEXT,
            memory_strength DECIMAL,
            priority_score DECIMAL
        ) AS $$
        BEGIN
            RETURN QUERY
            WITH assignment_contents AS (
                -- Get all content_items for this assignment
                SELECT DISTINCT ci.id as content_item_id
                FROM student_assignments sa
                JOIN student_content_progress scp ON scp.student_assignment_id = sa.id
                JOIN content_items ci ON ci.content_id = scp.content_id
                WHERE sa.id = p_student_assignment_id
            )
            SELECT
                ci.id,
                ci.text,
                ci.translation,
                ci.example_sentence,
                ci.example_sentence_translation,
                ci.audio_url,
                COALESCE(uwp.memory_strength, 0) as memory_strength,
                -- Priority calculation:
                -- 1. Never practiced (priority = 100)
                -- 2. Due for review + low memory (priority = 50-100)
                -- 3. Not due but low memory (priority = 0-30)
                CASE
                    WHEN uwp.id IS NULL THEN 100  -- Never practiced
                    WHEN uwp.next_review_at IS NULL THEN 100
                    WHEN uwp.next_review_at <= NOW() THEN
                        50 + (1 - uwp.memory_strength) * 50
                    ELSE
                        (1 - uwp.memory_strength) * 30
                END as priority_score
            FROM assignment_contents ac
            JOIN content_items ci ON ci.id = ac.content_item_id
            LEFT JOIN user_word_progress uwp ON
                uwp.student_assignment_id = p_student_assignment_id AND
                uwp.content_item_id = ci.id
            ORDER BY priority_score DESC, RANDOM()
            LIMIT p_limit_count;
        END;
        $$ LANGUAGE plpgsql;
    """
    )
