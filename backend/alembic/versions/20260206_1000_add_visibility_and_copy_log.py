"""Add visibility to programs and program_copy_logs table

Revision ID: 20260206_1000
Revises: 20260205_1800
Create Date: 2026-02-06 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260206_1000"
down_revision = "20260205_1800"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add visibility column to programs (idempotent)
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                          WHERE table_name = 'programs' AND column_name = 'visibility') THEN
                ALTER TABLE programs ADD COLUMN visibility VARCHAR(20) NOT NULL DEFAULT 'private';
            END IF;
        END $$;
    """
    )

    # 2. Create program_copy_logs table (idempotent)
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS program_copy_logs (
            id SERIAL PRIMARY KEY,
            source_program_id INTEGER NOT NULL REFERENCES programs(id) ON DELETE RESTRICT,
            copied_by_type VARCHAR(20) NOT NULL,
            copied_by_id VARCHAR(100) NOT NULL,
            copied_program_id INTEGER REFERENCES programs(id) ON DELETE SET NULL,
            copied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """
    )

    # 3. Create indexes (idempotent)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_program_copy_logs_source "
        "ON program_copy_logs (source_program_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_program_copy_logs_copied_by "
        "ON program_copy_logs (copied_by_type, copied_by_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_program_copy_logs_copied_at "
        "ON program_copy_logs (copied_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_programs_visibility " "ON programs (visibility)"
    )


def downgrade() -> None:
    pass
