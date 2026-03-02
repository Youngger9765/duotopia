"""Backfill distractors for word_selection assignments

One-time data migration: for all word_selection assignments,
fill in missing distractors using other words' translations
from the same content.

Handles: distractors IS NULL, distractors = '[]', distractors = 'null' (string)

Revision ID: 20260302_1000
Revises: 20260227_1000
Create Date: 2026-03-02 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260302_1000"
down_revision = "20260227_1000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Backfill distractors for word_selection assignments
    # Uses other words' translations from the same content as distractors
    # Idempotent: only updates items that have NULL, empty, or "null" distractors
    op.execute(
        """
        WITH word_selection_contents AS (
            -- Find all content copies linked to word_selection assignments
            SELECT DISTINCT ac.content_id
            FROM assignments a
            JOIN assignment_contents ac ON ac.assignment_id = a.id
            WHERE a.practice_mode = 'word_selection'
        ),
        items_needing_distractors AS (
            -- Find content items that need distractors
            SELECT ci.id, ci.content_id, ci.translation
            FROM content_items ci
            JOIN word_selection_contents wsc ON wsc.content_id = ci.content_id
            WHERE ci.translation IS NOT NULL
              AND ci.translation != ''
              -- NULL: never set; '[]': empty array;
              -- 'null': JSON null keyword; '"null"': JSONB-serialised string
              AND (
                  ci.distractors IS NULL
                  OR ci.distractors::text = '[]'
                  OR ci.distractors::text = 'null'
                  OR ci.distractors::text = '"null"'
              )
        ),
        available_translations AS (
            -- For each content, collect all translations (for picking distractors)
            SELECT ci.content_id, ci.id AS item_id,
                   LOWER(TRIM(ci.translation)) AS normalized,
                   ci.translation AS original
            FROM content_items ci
            JOIN word_selection_contents wsc ON wsc.content_id = ci.content_id
            WHERE ci.translation IS NOT NULL
              AND ci.translation != ''
        ),
        distractors_for_items AS (
            -- For each item needing distractors, pick up to 3 random translations
            -- from other words in the same content
            SELECT
                ind.id AS item_id,
                (
                    SELECT jsonb_agg(sub.original)
                    FROM (
                        SELECT at2.original
                        FROM available_translations at2
                        WHERE at2.content_id = ind.content_id
                          AND at2.normalized != LOWER(TRIM(ind.translation))
                        ORDER BY random()
                        LIMIT 3
                    ) sub
                ) AS new_distractors
            FROM items_needing_distractors ind
        )
        UPDATE content_items ci
        SET distractors = dfi.new_distractors
        FROM distractors_for_items dfi
        WHERE ci.id = dfi.item_id
          AND dfi.new_distractors IS NOT NULL
          AND jsonb_array_length(dfi.new_distractors) > 0;
    """
    )


def downgrade() -> None:
    # Data migration - no schema rollback needed
    # Distractors are not removed on downgrade as they don't break anything
    pass
