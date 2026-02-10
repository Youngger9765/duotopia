"""add_rls_to_organization_points_log

Revision ID: 20260203_1600
Revises: 238cc2af0367
Create Date: 2026-02-03 16:00:00

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260203_1600"
down_revision = "238cc2af0367"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Enable RLS on organization_points_log table.
    Idempotent - safe to run multiple times.
    """
    # Enable RLS on organization_points_log if it exists
    op.execute(
        """
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'organization_points_log'
                  AND table_schema = 'public'
            ) THEN
                -- Check if RLS is already enabled
                IF NOT (
                    SELECT relrowsecurity
                    FROM pg_class
                    WHERE relname = 'organization_points_log'
                      AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                ) THEN
                    ALTER TABLE organization_points_log ENABLE ROW LEVEL SECURITY;
                END IF;
            END IF;
        END $$;
    """
    )


def downgrade() -> None:
    """
    Disable RLS on organization_points_log table.
    """
    op.execute(
        """
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'organization_points_log'
                  AND table_schema = 'public'
            ) THEN
                ALTER TABLE organization_points_log DISABLE ROW LEVEL SECURITY;
            END IF;
        END $$;
    """
    )
