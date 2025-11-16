"""add_sentence_making_phase1_tables_and_functions

Revision ID: 666c291b851d
Revises: 1016469bbf26
Create Date: 2025-11-12 10:45:50.114078

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '666c291b851d'
down_revision: Union[str, None] = '1016469bbf26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================
    # Phase 1: Sentence Making Feature - Database Schema
    # ========================================

    # 1. Add answer_mode column to assignments table
    # CRITICAL: Must have DEFAULT 'writing' for backward compatibility
    op.execute("""
        ALTER TABLE assignments
        ADD COLUMN IF NOT EXISTS answer_mode VARCHAR(20)
        DEFAULT 'writing'
        CHECK (answer_mode IN ('listening', 'writing'))
    """)

    # 2. Create user_word_progress table (核心記憶追蹤表)
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_word_progress (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            student_assignment_id INTEGER NOT NULL REFERENCES student_assignments(id) ON DELETE CASCADE,
            content_item_id INTEGER NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,

            -- 艾賓浩斯記憶曲線相關欄位
            memory_strength NUMERIC(5, 4) DEFAULT 0 NOT NULL,
            repetition_count INTEGER DEFAULT 0 NOT NULL,
            correct_count INTEGER DEFAULT 0 NOT NULL,
            incorrect_count INTEGER DEFAULT 0 NOT NULL,
            last_review_at TIMESTAMPTZ,
            next_review_at TIMESTAMPTZ,
            easiness_factor NUMERIC(3, 2) DEFAULT 2.5 NOT NULL,
            interval_days NUMERIC(10, 2) DEFAULT 1 NOT NULL,
            total_attempts INTEGER DEFAULT 0 NOT NULL,
            accuracy_rate NUMERIC(5, 4) DEFAULT 0 NOT NULL,

            created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

            CONSTRAINT uq_user_word_progress_assignment_item
                UNIQUE (student_assignment_id, content_item_id),
            CONSTRAINT check_memory_strength_range
                CHECK (memory_strength >= 0 AND memory_strength <= 1),
            CONSTRAINT check_easiness_factor_min
                CHECK (easiness_factor >= 1.3)
        )
    """)

    # Create indexes for user_word_progress
    op.execute("CREATE INDEX IF NOT EXISTS idx_user_word_progress_student ON user_word_progress (student_id, student_assignment_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_user_word_progress_next_review ON user_word_progress (student_assignment_id, next_review_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_user_word_progress_memory ON user_word_progress (memory_strength)")

    # 3. Create practice_sessions table
    op.execute("""
        CREATE TABLE IF NOT EXISTS practice_sessions (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            student_assignment_id INTEGER NOT NULL REFERENCES student_assignments(id) ON DELETE CASCADE,
            practice_mode VARCHAR(20) NOT NULL,
            words_practiced INTEGER DEFAULT 0 NOT NULL,
            correct_count INTEGER DEFAULT 0 NOT NULL,
            total_time_seconds INTEGER DEFAULT 0 NOT NULL,
            started_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

            CONSTRAINT check_practice_mode CHECK (practice_mode IN ('listening', 'writing'))
        )
    """)

    # Create indexes for practice_sessions
    op.execute("CREATE INDEX IF NOT EXISTS idx_practice_sessions_student ON practice_sessions (student_id, student_assignment_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_practice_sessions_started ON practice_sessions (started_at)")

    # 4. Create practice_answers table
    op.execute("""
        CREATE TABLE IF NOT EXISTS practice_answers (
            id SERIAL PRIMARY KEY,
            practice_session_id INTEGER NOT NULL REFERENCES practice_sessions(id) ON DELETE CASCADE,
            content_item_id INTEGER NOT NULL REFERENCES content_items(id),
            is_correct BOOLEAN NOT NULL,
            time_spent_seconds INTEGER DEFAULT 0 NOT NULL,
            answer_data JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
        )
    """)

    # Create indexes for practice_answers
    op.execute("CREATE INDEX IF NOT EXISTS idx_practice_answers_session ON practice_answers (practice_session_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_practice_answers_item ON practice_answers (content_item_id)")

    # ========================================
    # PostgreSQL Functions for Ebbinghaus Memory Curve
    # ========================================

    # Function 1: update_memory_strength - Core SM-2 Algorithm
    op.execute("""
        CREATE OR REPLACE FUNCTION update_memory_strength(
            p_student_assignment_id INTEGER,
            p_content_item_id INTEGER,
            p_is_correct BOOLEAN
        ) RETURNS TABLE (
            memory_strength DECIMAL,
            next_review_at TIMESTAMPTZ,
            easiness_factor DECIMAL,
            repetition_count INTEGER
        ) AS $$
        DECLARE
            v_progress user_word_progress%ROWTYPE;
            v_time_since_last_review INTERVAL;
            v_new_strength DECIMAL;
            v_new_easiness DECIMAL;
            v_new_interval DECIMAL;
            v_practiced_words INTEGER;
            v_student_id INTEGER;
        BEGIN
            -- Get or create progress record
            SELECT * INTO v_progress
            FROM user_word_progress
            WHERE student_assignment_id = p_student_assignment_id
                AND content_item_id = p_content_item_id;

            -- If not found, create new record
            IF NOT FOUND THEN
                -- Get student_id from student_assignment
                SELECT sa.student_id INTO v_student_id
                FROM student_assignments sa
                WHERE sa.id = p_student_assignment_id;

                INSERT INTO user_word_progress (
                    student_id,
                    student_assignment_id,
                    content_item_id,
                    memory_strength,
                    last_review_at,
                    next_review_at,
                    total_attempts,
                    correct_count,
                    incorrect_count,
                    repetition_count
                ) VALUES (
                    v_student_id,
                    p_student_assignment_id,
                    p_content_item_id,
                    CASE WHEN p_is_correct THEN 0.5 ELSE 0.2 END,
                    NOW(),
                    NOW() + INTERVAL '1 day',
                    1,
                    CASE WHEN p_is_correct THEN 1 ELSE 0 END,
                    CASE WHEN p_is_correct THEN 0 ELSE 1 END,
                    CASE WHEN p_is_correct THEN 1 ELSE 0 END
                )
                RETURNING * INTO v_progress;

                RETURN QUERY SELECT
                    v_progress.memory_strength,
                    v_progress.next_review_at,
                    v_progress.easiness_factor,
                    v_progress.repetition_count;
                RETURN;
            END IF;

            -- Calculate time since last review
            v_time_since_last_review := NOW() - COALESCE(v_progress.last_review_at, NOW());

            -- Ebbinghaus forgetting curve: R = e^(-t/S)
            -- R: retention rate, t: time elapsed (seconds), S: strength constant (proportional to easiness)
            v_new_strength := v_progress.memory_strength *
                EXP(
                    -EXTRACT(EPOCH FROM v_time_since_last_review) /
                    (86400.0 * v_progress.easiness_factor)
                );

            IF p_is_correct THEN
                -- ===== Correct Answer Processing =====

                -- Increase memory strength (max 1.0)
                v_new_strength := LEAST(1.0, v_new_strength + 0.3);

                -- Update easiness factor (SM-2 algorithm)
                -- EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
                -- where q = 4 (quality rating for correct answer)
                v_new_easiness := v_progress.easiness_factor +
                    (0.1 - (5 - 4) * (0.08 + (5 - 4) * 0.02));
                v_new_easiness := GREATEST(1.3, v_new_easiness);

                -- Calculate next review interval (SM-2 algorithm)
                IF v_progress.repetition_count = 0 THEN
                    v_new_interval := 1;  -- First correct: review in 1 day
                ELSIF v_progress.repetition_count = 1 THEN
                    v_new_interval := 6;  -- Second correct: review in 6 days
                ELSE
                    v_new_interval := v_progress.interval_days * v_new_easiness;
                END IF;

                -- Update record
                UPDATE user_word_progress SET
                    memory_strength = v_new_strength,
                    repetition_count = repetition_count + 1,
                    correct_count = correct_count + 1,
                    total_attempts = total_attempts + 1,
                    easiness_factor = v_new_easiness,
                    interval_days = v_new_interval,
                    last_review_at = NOW(),
                    next_review_at = NOW() + (v_new_interval || ' days')::INTERVAL,
                    accuracy_rate = (correct_count + 1)::DECIMAL / (total_attempts + 1),
                    updated_at = NOW()
                WHERE id = v_progress.id
                RETURNING * INTO v_progress;

            ELSE
                -- ===== Incorrect Answer Processing =====

                -- Decrease memory strength
                v_new_strength := GREATEST(0.1, v_new_strength * 0.5);

                -- Decrease easiness factor (harder to remember)
                v_new_easiness := GREATEST(1.3, v_progress.easiness_factor - 0.2);

                -- Reset interval to 1 day
                v_new_interval := 1;

                UPDATE user_word_progress SET
                    memory_strength = v_new_strength,
                    repetition_count = 0,  -- Reset consecutive correct count
                    incorrect_count = incorrect_count + 1,
                    total_attempts = total_attempts + 1,
                    easiness_factor = v_new_easiness,
                    interval_days = v_new_interval,
                    last_review_at = NOW(),
                    next_review_at = NOW() + INTERVAL '1 day',
                    accuracy_rate = correct_count::DECIMAL / (total_attempts + 1),
                    updated_at = NOW()
                WHERE id = v_progress.id
                RETURNING * INTO v_progress;
            END IF;

            RETURN QUERY SELECT
                v_progress.memory_strength,
                v_progress.next_review_at,
                v_progress.easiness_factor,
                v_progress.repetition_count;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Function 2: get_words_for_practice - Intelligent Word Selection
    op.execute("""
        CREATE OR REPLACE FUNCTION get_words_for_practice(
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
    """)

    # Function 3: calculate_assignment_mastery - Check Assignment Completion
    op.execute("""
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
            v_target DECIMAL := 0.90;
        BEGIN
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

            -- Count mastered words (memory_strength >= 0.8)
            SELECT COUNT(*) INTO v_words_mastered
            FROM user_word_progress
            WHERE student_assignment_id = p_student_assignment_id
                AND memory_strength >= 0.8;

            RETURN QUERY SELECT
                v_avg_strength,
                v_target,
                v_avg_strength >= v_target,
                v_words_mastered,
                v_total_words;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    # Drop PostgreSQL functions
    op.execute("DROP FUNCTION IF EXISTS calculate_assignment_mastery")
    op.execute("DROP FUNCTION IF EXISTS get_words_for_practice")
    op.execute("DROP FUNCTION IF EXISTS update_memory_strength")

    # Drop tables (reverse order to respect foreign keys)
    op.drop_table('practice_answers')
    op.drop_table('practice_sessions')
    op.drop_table('user_word_progress')

    # Remove answer_mode column from assignments
    op.drop_column('assignments', 'answer_mode')
