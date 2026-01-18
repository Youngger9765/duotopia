"""Add tax_id column to organizations table

Revision ID: f8a7c3d2e1b0
Revises: ed63e979dc1c
Create Date: 2026-01-10 14:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f8a7c3d2e1b0"
down_revision = "ed63e979dc1c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add tax_id column to organizations table (if table exists)
    # Skip if table doesn't exist (develop environment)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'organizations') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                              WHERE table_name = 'organizations' AND column_name = 'tax_id') THEN
                    ALTER TABLE organizations ADD COLUMN tax_id VARCHAR(20);
                END IF;

                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_organizations_tax_id') THEN
                    ALTER TABLE organizations ADD CONSTRAINT uq_organizations_tax_id UNIQUE (tax_id);
                END IF;

                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_organizations_tax_id') THEN
                    CREATE INDEX ix_organizations_tax_id ON organizations (tax_id);
                END IF;
            END IF;
        END $$;
    """
    )


def downgrade() -> None:
    # Remove index, constraint, and column (if table exists)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'organizations') THEN
                DROP INDEX IF EXISTS ix_organizations_tax_id;
                ALTER TABLE organizations DROP CONSTRAINT IF EXISTS uq_organizations_tax_id;
                ALTER TABLE organizations DROP COLUMN IF EXISTS tax_id;
            END IF;
        END $$;
    """
    )
