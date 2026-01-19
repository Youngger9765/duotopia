"""add_image_url_to_get_words_for_practice

Revision ID: f8c2d3e4a5b6
Revises: 9a698a17a016
Create Date: 2026-01-14 03:09:00.000000

Fix: Add image_url column to get_words_for_practice function
so that student word selection activity can display images.
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f8c2d3e4a5b6"
down_revision: Union[str, None] = "9a698a17a016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL doesn't allow changing return types with CREATE OR REPLACE
    # Must DROP first, then CREATE
    op.execute("DROP FUNCTION IF EXISTS get_words_for_practice(INTEGER, INTEGER)")

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
            image_url TEXT,
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
                ci.image_url,
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
    # Restore the old function without image_url
    op.execute("DROP FUNCTION IF EXISTS get_words_for_practice(INTEGER, INTEGER)")

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
                CASE
                    WHEN uwp.id IS NULL THEN 100
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
