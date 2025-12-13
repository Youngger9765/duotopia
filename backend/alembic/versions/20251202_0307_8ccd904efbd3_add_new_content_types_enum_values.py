"""add_new_content_types_enum_values

Add new ContentType enum values for Phase 1 and Phase 2:
- EXAMPLE_SENTENCES (例句集) - Phase 1, replaces READING_ASSESSMENT
- VOCABULARY_SET (單字集) - Phase 2, replaces SENTENCE_MAKING
- MULTIPLE_CHOICE (單選題庫) - Phase 2
- SCENARIO_DIALOGUE (情境對話) - Phase 2

Revision ID: 8ccd904efbd3
Revises: 645f464ffb30
Create Date: 2025-12-02 03:07:57.808750

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8ccd904efbd3"
down_revision: Union[str, None] = "645f464ffb30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new ContentType enum values using IF NOT EXISTS pattern
    # This ensures compatibility with shared database environments (develop/staging)
    op.execute(
        """
        DO $$
        BEGIN
            -- Add EXAMPLE_SENTENCES (例句集 - Phase 1)
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumlabel = 'EXAMPLE_SENTENCES'
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'contenttype')
            ) THEN
                ALTER TYPE contenttype ADD VALUE 'EXAMPLE_SENTENCES';
            END IF;

            -- Add VOCABULARY_SET (單字集 - Phase 2)
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumlabel = 'VOCABULARY_SET'
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'contenttype')
            ) THEN
                ALTER TYPE contenttype ADD VALUE 'VOCABULARY_SET';
            END IF;

            -- Add MULTIPLE_CHOICE (單選題庫 - Phase 2)
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumlabel = 'MULTIPLE_CHOICE'
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'contenttype')
            ) THEN
                ALTER TYPE contenttype ADD VALUE 'MULTIPLE_CHOICE';
            END IF;

            -- Add SCENARIO_DIALOGUE (情境對話 - Phase 2)
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumlabel = 'SCENARIO_DIALOGUE'
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'contenttype')
            ) THEN
                ALTER TYPE contenttype ADD VALUE 'SCENARIO_DIALOGUE';
            END IF;
        END
        $$;
    """
    )


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed, keeping as-is for safety
    pass
