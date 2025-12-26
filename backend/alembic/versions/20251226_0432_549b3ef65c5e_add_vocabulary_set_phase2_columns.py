"""add_vocabulary_set_phase2_columns

Revision ID: 549b3ef65c5e
Revises: cb0920d3ab63
Create Date: 2025-12-26 04:32:00.000000

Phase 2-1: Database extension for VOCABULARY_SET feature
- Add target_proficiency, show_translation, show_word, show_image to assignments
- Add image_url, part_of_speech to content_items
- Update calculate_assignment_mastery() to use configurable target_proficiency
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "549b3ef65c5e"
down_revision: Union[str, None] = "cb0920d3ab63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================
    # Phase 2-1: VOCABULARY_SET Feature - Database Extensions
    # ========================================

    # 1. Add VOCABULARY_SET specific columns to assignments table
    # CRITICAL: All columns must have DEFAULT values for backward compatibility

    # target_proficiency: Target mastery level for word_selection mode (default 80%)
    op.execute(
        """
        ALTER TABLE assignments
        ADD COLUMN IF NOT EXISTS target_proficiency INTEGER DEFAULT 80
    """
    )

    # show_translation: Whether to show word translation (default true)
    op.execute(
        """
        ALTER TABLE assignments
        ADD COLUMN IF NOT EXISTS show_translation BOOLEAN DEFAULT TRUE
    """
    )

    # show_word: Whether to show the word text (default true)
    op.execute(
        """
        ALTER TABLE assignments
        ADD COLUMN IF NOT EXISTS show_word BOOLEAN DEFAULT TRUE
    """
    )

    # show_image: Whether to show word image (default true)
    op.execute(
        """
        ALTER TABLE assignments
        ADD COLUMN IF NOT EXISTS show_image BOOLEAN DEFAULT TRUE
    """
    )

    # 2. Add VOCABULARY_SET specific columns to content_items table

    # image_url: URL to word image (for visual learning)
    op.execute(
        """
        ALTER TABLE content_items
        ADD COLUMN IF NOT EXISTS image_url TEXT
    """
    )

    # part_of_speech: Word class (n., v., adj., adv., etc.)
    op.execute(
        """
        ALTER TABLE content_items
        ADD COLUMN IF NOT EXISTS part_of_speech VARCHAR(20)
    """
    )

    # 3. Update calculate_assignment_mastery() to use configurable target_proficiency
    # This function now reads target_proficiency from the assignment table
    op.execute(
        """
        CREATE OR REPLACE FUNCTION calculate_assignment_mastery(
            p_student_assignment_id INTEGER
        ) RETURNS TABLE (
            current_mastery DECIMAL,
            target_mastery DECIMAL,
            achieved BOOLEAN,
            words_mastered INTEGER,
            total_words INTEGER
        ) AS $$
        DECLARE
            v_total_words INTEGER;
            v_practiced_words INTEGER;
            v_avg_strength DECIMAL;
            v_words_mastered INTEGER;
            v_target DECIMAL;
            v_target_proficiency INTEGER;
        BEGIN
            -- Get target_proficiency from assignment (default to 80 if not set)
            SELECT COALESCE(a.target_proficiency, 80) INTO v_target_proficiency
            FROM student_assignments sa
            JOIN assignments a ON a.id = sa.assignment_id
            WHERE sa.id = p_student_assignment_id;

            -- Convert percentage to decimal (80 -> 0.80)
            v_target := v_target_proficiency / 100.0;

            -- Get total word count for assignment
            SELECT COUNT(DISTINCT ci.id) INTO v_total_words
            FROM student_assignments sa
            JOIN student_content_progress scp ON scp.student_assignment_id = sa.id
            JOIN content_items ci ON ci.content_id = scp.content_id
            WHERE sa.id = p_student_assignment_id;

            IF v_total_words = 0 THEN
                RETURN QUERY SELECT 0::DECIMAL, v_target, FALSE, 0, 0;
                RETURN;
            END IF;

            -- Calculate average memory strength
            SELECT
                COALESCE(AVG(uwp.memory_strength), 0),
                COUNT(*)
            INTO v_avg_strength, v_practiced_words
            FROM user_word_progress uwp
            WHERE uwp.student_assignment_id = p_student_assignment_id;

            -- Adjust for unpracticed words (treat as 0 strength)
            IF v_practiced_words < v_total_words THEN
                v_avg_strength := (v_avg_strength * v_practiced_words) / v_total_words;
            END IF;

            -- Count mastered words (memory_strength >= target * 0.8)
            -- Using 80% of target as "mastered" threshold
            SELECT COUNT(*) INTO v_words_mastered
            FROM user_word_progress
            WHERE student_assignment_id = p_student_assignment_id
                AND memory_strength >= (v_target * 0.8);

            RETURN QUERY SELECT
                v_avg_strength,
                v_target,
                v_avg_strength >= v_target,
                v_words_mastered,
                v_total_words;
        END;
        $$ LANGUAGE plpgsql;
    """
    )


def downgrade() -> None:
    # Note: Following additive-only migration principle
    # We don't drop columns or revert function changes
    # The old function signature is compatible with new one
    pass
