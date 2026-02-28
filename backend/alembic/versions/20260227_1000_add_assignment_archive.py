"""Add is_archived and archived_at columns to assignments

Revision ID: 20260227_1000
Revises: 20260225_1600
Create Date: 2026-02-27 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260227_1000"
down_revision = "20260225_1600"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_archived column (idempotent)
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                          WHERE table_name = 'assignments' AND column_name = 'is_archived') THEN
                ALTER TABLE assignments ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT FALSE;
            END IF;
        END $$;
    """
    )

    # Add archived_at column (idempotent)
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                          WHERE table_name = 'assignments' AND column_name = 'archived_at') THEN
                ALTER TABLE assignments ADD COLUMN archived_at TIMESTAMPTZ;
            END IF;
        END $$;
    """
    )

    # Add index for faster archive queries (idempotent)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_assignments_is_archived ON assignments (is_archived)"
    )


def downgrade() -> None:
    pass
