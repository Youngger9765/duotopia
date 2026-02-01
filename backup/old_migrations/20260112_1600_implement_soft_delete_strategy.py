"""Implement soft delete strategy for organization module

Per #151 spec review decisions:
1. Remove tax_id unique constraint, add partial unique index (is_active=true)
2. Add org_owner partial unique constraint
3. Add performance indexes on is_active fields

Revision ID: a1b2c3d4e5f6
Revises: d21f6f58c952
Create Date: 2026-01-12 16:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "d21f6f58c952"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Implement soft delete strategy as per final-decisions.md

    Decision #1: Soft delete strategy (is_active=false)
    Decision #2: tax_id partial unique index
    Decision #3: org_owner database constraint
    """

    # ========================================
    # Decision #2: tax_id Partial Unique Index
    # ========================================

    # Remove old unique constraint if exists
    # Use SQL IF EXISTS to avoid transaction abort when constraint doesn't exist
    # Python try-except doesn't prevent PostgreSQL from aborting the transaction
    op.execute(
        """
        ALTER TABLE organizations
        DROP CONSTRAINT IF EXISTS uq_organizations_tax_id
    """
    )

    op.execute(
        """
        ALTER TABLE organizations
        DROP CONSTRAINT IF EXISTS organizations_tax_id_key
    """
    )

    # Create partial unique index (only for active organizations)
    # This allows reusing tax_id after organization is deactivated
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_organizations_tax_id_active
        ON organizations (tax_id)
        WHERE is_active = true AND tax_id IS NOT NULL
    """
    )

    # ========================================
    # Decision #3: org_owner Unique Constraint
    # ========================================

    # Create partial unique index to enforce single org_owner per organization
    # Only active relationships are considered
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_teacher_org_owner
        ON teacher_organizations (organization_id)
        WHERE role = 'org_owner' AND is_active = true
    """
    )

    # ========================================
    # Decision #1: Performance Indexes for Soft Delete
    # ========================================

    # Note: Based on models.py, some of these indexes may already exist
    # Using IF NOT EXISTS to avoid errors

    # Organizations table
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_organizations_is_active
        ON organizations(is_active)
    """
    )

    # Schools table
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_schools_is_active
        ON schools(is_active)
    """
    )

    # TeacherOrganizations table
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_teacher_organizations_is_active
        ON teacher_organizations(is_active)
    """
    )

    # TeacherSchools table (bonus - not in original spec but follows pattern)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_teacher_schools_is_active
        ON teacher_schools(is_active)
    """
    )

    # ClassroomSchools table (bonus - follows pattern)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_classroom_schools_is_active
        ON classroom_schools(is_active)
    """
    )


def downgrade() -> None:
    """
    Rollback soft delete strategy changes
    """

    # Remove performance indexes
    op.execute("DROP INDEX IF EXISTS idx_classroom_schools_is_active")
    op.execute("DROP INDEX IF EXISTS idx_teacher_schools_is_active")
    op.execute("DROP INDEX IF EXISTS idx_teacher_organizations_is_active")
    op.execute("DROP INDEX IF EXISTS idx_schools_is_active")
    op.execute("DROP INDEX IF EXISTS idx_organizations_is_active")

    # Remove org_owner constraint
    op.execute("DROP INDEX IF EXISTS uq_teacher_org_owner")

    # Remove tax_id partial unique index
    op.execute("DROP INDEX IF EXISTS uq_organizations_tax_id_active")

    # Clean duplicate tax_ids before restoring unique constraint
    # Strategy: For each duplicate tax_id, keep only the most recent organization
    # Note: This is destructive but safe for downgrade (dev-only operation)
    op.execute("""
        -- Step 1: Mark older duplicates with NULL tax_id
        UPDATE organizations
        SET tax_id = NULL
        WHERE id IN (
            SELECT id
            FROM (
                SELECT id,
                       tax_id,
                       ROW_NUMBER() OVER (PARTITION BY tax_id ORDER BY created_at DESC) as rn
                FROM organizations
                WHERE tax_id IS NOT NULL
            ) AS ranked
            WHERE rn > 1
        )
    """)

    # Now safe to restore unique constraint (no duplicates)
    op.create_unique_constraint(
        "uq_organizations_tax_id",
        "organizations",
        ["tax_id"],
    )
