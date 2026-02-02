"""Add organization points system

Revision ID: 20260203_0143
Revises: 20260128_fix_auto_graded_historical_data
Create Date: 2026-02-03 01:43:00

Adds:
1. Points tracking columns to organizations table
2. organization_points_log table for audit trail

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260203_0143'
down_revision = '20260128_fix_auto_graded_historical_data'
branch_labels = None
depends_on = None


def upgrade():
    """
    Idempotent migration for organization points system.
    Safe to run multiple times.
    """

    # Add points columns to organizations table
    op.execute("""
        DO $$ BEGIN
            -- Add total_points column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'organizations' AND column_name = 'total_points'
            ) THEN
                ALTER TABLE organizations ADD COLUMN total_points INTEGER DEFAULT 0 NOT NULL;
            END IF;

            -- Add used_points column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'organizations' AND column_name = 'used_points'
            ) THEN
                ALTER TABLE organizations ADD COLUMN used_points INTEGER DEFAULT 0 NOT NULL;
            END IF;

            -- Add last_points_update column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'organizations' AND column_name = 'last_points_update'
            ) THEN
                ALTER TABLE organizations ADD COLUMN last_points_update TIMESTAMP WITH TIME ZONE;
            END IF;
        END $$;
    """)

    # Create organization_points_log table
    op.execute("""
        CREATE TABLE IF NOT EXISTS organization_points_log (
            id SERIAL PRIMARY KEY,
            organization_id UUID NOT NULL,
            teacher_id INTEGER,
            points_used INTEGER NOT NULL,
            feature_type VARCHAR(50),
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
        );
    """)

    # Add foreign key constraints (only if not exists)
    op.execute("""
        DO $$ BEGIN
            -- Add FK constraint for organization_id
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_organization_points_log_organization_id'
            ) THEN
                ALTER TABLE organization_points_log
                ADD CONSTRAINT fk_organization_points_log_organization_id
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;
            END IF;

            -- Add FK constraint for teacher_id
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_organization_points_log_teacher_id'
            ) THEN
                ALTER TABLE organization_points_log
                ADD CONSTRAINT fk_organization_points_log_teacher_id
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL;
            END IF;
        END $$;
    """)

    # Create indexes for performance
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_organization_points_log_organization_id
        ON organization_points_log(organization_id);

        CREATE INDEX IF NOT EXISTS ix_organization_points_log_teacher_id
        ON organization_points_log(teacher_id);

        CREATE INDEX IF NOT EXISTS ix_organization_points_log_created_at
        ON organization_points_log(created_at DESC);
    """)

    # Add check constraint to ensure used_points doesn't exceed total_points
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'chk_organizations_points_valid'
            ) THEN
                ALTER TABLE organizations
                ADD CONSTRAINT chk_organizations_points_valid
                CHECK (used_points <= total_points AND used_points >= 0 AND total_points >= 0);
            END IF;
        END $$;
    """)


def downgrade():
    """
    Rollback migration.
    Note: This is destructive and will lose data.
    """
    # Drop check constraint
    op.execute("""
        ALTER TABLE organizations DROP CONSTRAINT IF EXISTS chk_organizations_points_valid;
    """)

    # Drop indexes
    op.execute("""
        DROP INDEX IF EXISTS ix_organization_points_log_created_at;
        DROP INDEX IF EXISTS ix_organization_points_log_teacher_id;
        DROP INDEX IF EXISTS ix_organization_points_log_organization_id;
    """)

    # Drop table (cascades foreign keys)
    op.execute("""
        DROP TABLE IF EXISTS organization_points_log CASCADE;
    """)

    # Drop columns from organizations
    op.execute("""
        ALTER TABLE organizations DROP COLUMN IF EXISTS last_points_update;
        ALTER TABLE organizations DROP COLUMN IF EXISTS used_points;
        ALTER TABLE organizations DROP COLUMN IF EXISTS total_points;
    """)
