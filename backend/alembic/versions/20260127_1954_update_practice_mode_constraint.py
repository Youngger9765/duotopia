"""Update check_practice_mode constraint to include word_selection

The practice_sessions table has a CHECK constraint that only allows
'listening' and 'writing' modes in some environments. Production was
manually updated to include 'word_selection', but staging/develop
still have the old constraint. This migration ensures all environments
have the same constraint.

Revision ID: f1a2b3c4d5e6
Revises: ae8fd7c7cc74
Create Date: 2026-01-27 19:54:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "f1a2b3c4d5e6"
down_revision = "ae8fd7c7cc74"
branch_labels = None
depends_on = None


def upgrade():
    """Update check_practice_mode constraint to include word_selection."""
    # Drop existing constraint and add new one with updated values
    # Using IF EXISTS for idempotency - safe to run on production
    # where constraint already includes word_selection
    op.execute(
        """
        DO $$ BEGIN
            -- Drop the existing constraint if it exists
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'check_practice_mode'
            ) THEN
                ALTER TABLE practice_sessions DROP CONSTRAINT check_practice_mode;
            END IF;

            -- Add the new constraint with updated values
            ALTER TABLE practice_sessions
            ADD CONSTRAINT check_practice_mode
            CHECK (practice_mode IN ('listening', 'writing', 'word_selection'));
        END $$;
    """
    )


def downgrade():
    """Revert to original constraint (listening, writing only)."""
    op.execute(
        """
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'check_practice_mode'
            ) THEN
                ALTER TABLE practice_sessions DROP CONSTRAINT check_practice_mode;
            END IF;

            ALTER TABLE practice_sessions
            ADD CONSTRAINT check_practice_mode
            CHECK (practice_mode IN ('listening', 'writing'));
        END $$;
    """
    )
