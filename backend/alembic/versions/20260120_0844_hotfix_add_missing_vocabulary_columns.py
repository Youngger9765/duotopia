"""hotfix_add_missing_vocabulary_columns

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-20 08:44:00.000000

Hotfix: Re-apply missing columns from 549b3ef65c5e migration.

The original migration was skipped due to CI/CD stamping the database
when orphaned alembic revision was detected. This hotfix uses
IF NOT EXISTS to safely add missing columns.

Missing columns that caused staging 500 errors:
- content_items.image_url
- content_items.part_of_speech
- assignments.target_proficiency
- assignments.show_translation
- assignments.show_word
- assignments.show_image
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================
    # Hotfix: Add missing VOCABULARY_SET columns
    # All use IF NOT EXISTS for idempotent execution
    # ========================================

    # 1. Add missing columns to assignments table
    op.execute(
        """
        ALTER TABLE assignments
        ADD COLUMN IF NOT EXISTS target_proficiency INTEGER DEFAULT 80
    """
    )

    op.execute(
        """
        ALTER TABLE assignments
        ADD COLUMN IF NOT EXISTS show_translation BOOLEAN DEFAULT TRUE
    """
    )

    op.execute(
        """
        ALTER TABLE assignments
        ADD COLUMN IF NOT EXISTS show_word BOOLEAN DEFAULT TRUE
    """
    )

    op.execute(
        """
        ALTER TABLE assignments
        ADD COLUMN IF NOT EXISTS show_image BOOLEAN DEFAULT TRUE
    """
    )

    # 2. Add missing columns to content_items table
    op.execute(
        """
        ALTER TABLE content_items
        ADD COLUMN IF NOT EXISTS image_url TEXT
    """
    )

    op.execute(
        """
        ALTER TABLE content_items
        ADD COLUMN IF NOT EXISTS part_of_speech VARCHAR(20)
    """
    )

    # 3. Update calculate_assignment_mastery() function
    # Using CREATE OR REPLACE for idempotent execution
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
    # Following additive-only migration principle
    # We don't drop columns
    pass
