"""Fix word selection repetition bug - phase-based selection

Revision ID: 20260303_1000
Revises: 20260302_1100
Create Date: 2026-03-03 10:00:00.000000

Fix: Rewrite get_words_for_practice to use explicit phase-based
selection (unpracticed -> due for review -> lowest strength) ensuring
unpracticed words are always selected first, preventing the same
10 words from repeating every round.

Related: #379
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260303_1000"
down_revision = "20260302_1100"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # DROP + CREATE because CREATE OR REPLACE is safer only when
    # we're certain the signature hasn't changed across environments
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
            WITH assignment_words AS (
                -- Get all content_items for this assignment
                SELECT DISTINCT ci.id as content_item_id
                FROM student_assignments sa
                JOIN student_content_progress scp
                    ON scp.student_assignment_id = sa.id
                JOIN content_items ci
                    ON ci.content_id = scp.content_id
                WHERE sa.id = p_student_assignment_id
            ),
            categorized AS (
                SELECT
                    ci.id,
                    ci.text,
                    ci.translation,
                    ci.example_sentence,
                    ci.example_sentence_translation,
                    ci.audio_url,
                    ci.image_url,
                    COALESCE(uwp.memory_strength, 0) as mem_strength,
                    -- Phase determines strict selection order:
                    --   1 = never practiced (always selected first)
                    --   2 = due for review   (selected second)
                    --   3 = not due yet      (selected last, weakest first)
                    CASE
                        WHEN uwp.id IS NULL THEN 1
                        WHEN uwp.next_review_at IS NULL THEN 1
                        WHEN uwp.next_review_at <= NOW() THEN 2
                        ELSE 3
                    END as phase
                FROM assignment_words aw
                JOIN content_items ci ON ci.id = aw.content_item_id
                LEFT JOIN user_word_progress uwp ON
                    uwp.student_assignment_id = p_student_assignment_id
                    AND uwp.content_item_id = ci.id
            )
            SELECT
                c.id as content_item_id,
                c.text,
                c.translation,
                c.example_sentence,
                c.example_sentence_translation,
                c.audio_url,
                c.image_url,
                c.mem_strength as memory_strength,
                -- Priority score kept for API response compatibility
                CASE c.phase
                    WHEN 1 THEN 100::DECIMAL
                    WHEN 2 THEN (50 + (1 - c.mem_strength) * 50)::DECIMAL
                    ELSE ((1 - c.mem_strength) * 30)::DECIMAL
                END as priority_score
            FROM categorized c
            -- KEY FIX (#379): Sort by phase ASC provides a hard guarantee:
            --   Phase 1 (unpracticed) ALWAYS before Phase 2 (due for review)
            --   Phase 2 ALWAYS before Phase 3 (not due yet)
            -- Within each phase, weakest words first, then random for variety
            ORDER BY c.phase ASC, c.mem_strength ASC, RANDOM()
            LIMIT p_limit_count;
        END;
        $$ LANGUAGE plpgsql;
    """
    )


def downgrade() -> None:
    # Restore previous version of the function
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
                SELECT DISTINCT ci.id as content_item_id
                FROM student_assignments sa
                JOIN student_content_progress scp
                    ON scp.student_assignment_id = sa.id
                JOIN content_items ci
                    ON ci.content_id = scp.content_id
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
