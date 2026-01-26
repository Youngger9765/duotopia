"""Add organization hierarchy and student management schema

Consolidates organization hierarchy and student relationship features:
- Soft delete strategy with partial indexes
- Teacher limit to organizations
- Organization/school ID to programs
- Content types enum expansion
- Classroom teacher nullable
- Student-school relationship table

All operations use IF NOT EXISTS / IF EXISTS for idempotency.
Safe to run even if staging DB already has these changes.

Revision ID: add_org_student_mgmt
Revises: d21f6f58c952
Create Date: 2026-01-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "add_org_student_mgmt"
down_revision = "d21f6f58c952"  # Last migration from staging
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add organization hierarchy and student management schema.
    All operations are idempotent using IF NOT EXISTS / IF EXISTS.
    """

    # ========================================
    # Part 1: Soft Delete Strategy (Migration 1)
    # ========================================

    # Drop tax_id unique constraints if they exist
    op.execute("""
        ALTER TABLE organizations
        DROP CONSTRAINT IF EXISTS uq_organizations_tax_id
    """)

    op.execute("""
        ALTER TABLE organizations
        DROP CONSTRAINT IF EXISTS organizations_tax_id_key
    """)

    # Create partial unique index for tax_id (active only)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_organizations_tax_id_active
        ON organizations (tax_id)
        WHERE is_active = true AND tax_id IS NOT NULL
    """)

    # Create org_owner unique constraint (active only)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_teacher_org_owner
        ON teacher_organizations (organization_id)
        WHERE role = 'org_owner' AND is_active = true
    """)

    # Create is_active indexes for performance
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_organizations_is_active
        ON organizations(is_active)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_schools_is_active
        ON schools(is_active)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_teacher_organizations_is_active
        ON teacher_organizations(is_active)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_teacher_schools_is_active
        ON teacher_schools(is_active)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_classroom_schools_is_active
        ON classroom_schools(is_active)
    """)

    # ========================================
    # Part 2: Teacher Limit Column (Migration 2)
    # ========================================

    # Add teacher_limit column if not exists
    # Note: Alembic doesn't have IF NOT EXISTS for add_column,
    # so we use raw SQL
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'organizations'
                AND column_name = 'teacher_limit'
            ) THEN
                ALTER TABLE organizations
                ADD COLUMN teacher_limit INTEGER NULL;
            END IF;
        END $$;
    """)

    # ========================================
    # Part 3: Organization ID to Programs (Migration 3)
    # ========================================

    # Add organization_id column if not exists
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'programs'
                AND column_name = 'organization_id'
            ) THEN
                ALTER TABLE programs
                ADD COLUMN organization_id UUID NULL;
            END IF;
        END $$;
    """)

    # Add FK constraint if not exists
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'fk_programs_organization_id'
            ) THEN
                ALTER TABLE programs
                ADD CONSTRAINT fk_programs_organization_id
                FOREIGN KEY (organization_id) REFERENCES organizations(id)
                ON DELETE CASCADE;
            END IF;
        END $$;
    """)

    # Add index if not exists
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_programs_organization_id
        ON programs(organization_id)
    """)

    # Data migration: Extract organization_id from source_metadata JSON
    # Only for template programs where source_metadata.organization_id exists
    # Safe to run multiple times (idempotent)
    op.execute("""
        UPDATE programs
        SET organization_id = CAST(source_metadata->>'organization_id' AS UUID)
        WHERE is_template = true
          AND organization_id IS NULL
          AND source_metadata IS NOT NULL
          AND CAST(source_metadata AS JSONB) ? 'organization_id'
          AND source_metadata->>'organization_id' IS NOT NULL
          AND source_metadata->>'organization_id' ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    """)

    # ========================================
    # Part 4: Content Types Enum (Migration 4)
    # ========================================

    # Add new enum values if not exists
    op.execute("ALTER TYPE contenttype ADD VALUE IF NOT EXISTS 'example_sentences'")
    op.execute("ALTER TYPE contenttype ADD VALUE IF NOT EXISTS 'vocabulary_set'")
    op.execute("ALTER TYPE contenttype ADD VALUE IF NOT EXISTS 'single_choice_quiz'")
    op.execute("ALTER TYPE contenttype ADD VALUE IF NOT EXISTS 'scenario_dialogue'")

    # ========================================
    # Part 5: School ID to Programs (Migration 5)
    # ========================================

    # Add school_id column if not exists
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'programs'
                AND column_name = 'school_id'
            ) THEN
                ALTER TABLE programs
                ADD COLUMN school_id UUID NULL;
            END IF;
        END $$;
    """)

    # Add FK constraint if not exists
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'fk_programs_school_id'
            ) THEN
                ALTER TABLE programs
                ADD CONSTRAINT fk_programs_school_id
                FOREIGN KEY (school_id) REFERENCES schools(id)
                ON DELETE CASCADE;
            END IF;
        END $$;
    """)

    # Add index if not exists
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_programs_school_id
        ON programs(school_id)
    """)

    # ========================================
    # Part 6: Classroom Teacher Nullable (Migration 6)
    # ========================================

    # Make teacher_id nullable if not already
    # Check current nullable status before attempting
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'classrooms'
                AND column_name = 'teacher_id'
                AND is_nullable = 'NO'
            ) THEN
                ALTER TABLE classrooms
                ALTER COLUMN teacher_id DROP NOT NULL;
            END IF;
        END $$;
    """)

    # ========================================
    # Part 7: Student Schools Table (Migration 7)
    # ========================================

    # Create student_schools table if not exists
    op.execute("""
        CREATE TABLE IF NOT EXISTS student_schools (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
            is_active BOOLEAN NOT NULL DEFAULT true,
            enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE,
            CONSTRAINT uq_student_school UNIQUE (student_id, school_id)
        )
    """)

    # Create indexes if not exists
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_student_schools_student_id
        ON student_schools(student_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_student_schools_school_id
        ON student_schools(school_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_student_schools_active
        ON student_schools(student_id, school_id, is_active)
    """)


def downgrade() -> None:
    """
    Rollback organization hierarchy and student management schema changes.

    WARNING: This is destructive and should only be used in development.
    Production downgrade requires careful data migration planning.
    """

    # Part 7: Drop student_schools table
    op.execute("DROP INDEX IF EXISTS ix_student_schools_active")
    op.execute("DROP INDEX IF EXISTS ix_student_schools_school_id")
    op.execute("DROP INDEX IF EXISTS ix_student_schools_student_id")
    op.execute("DROP TABLE IF EXISTS student_schools")

    # Part 6: Make classroom teacher_id non-nullable
    # WARNING: This will fail if there are NULL values
    # Check before downgrade:
    # SELECT COUNT(*) FROM classrooms WHERE teacher_id IS NULL;
    op.execute("""
        DO $$
        DECLARE
            null_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO null_count
            FROM classrooms
            WHERE teacher_id IS NULL;

            IF null_count > 0 THEN
                RAISE EXCEPTION 'Cannot downgrade: % classrooms have NULL teacher_id', null_count;
            END IF;

            ALTER TABLE classrooms
            ALTER COLUMN teacher_id SET NOT NULL;
        END $$;
    """)

    # Part 5: Drop school_id from programs
    op.execute("DROP INDEX IF EXISTS ix_programs_school_id")
    op.execute("ALTER TABLE programs DROP CONSTRAINT IF EXISTS fk_programs_school_id")
    op.execute("ALTER TABLE programs DROP COLUMN IF EXISTS school_id")

    # Part 4: Content types enum
    # Note: PostgreSQL doesn't support dropping enum values
    # Values will remain but won't be used
    pass

    # Part 3: Drop organization_id from programs
    op.execute("DROP INDEX IF EXISTS ix_programs_organization_id")
    op.execute("ALTER TABLE programs DROP CONSTRAINT IF EXISTS fk_programs_organization_id")
    op.execute("ALTER TABLE programs DROP COLUMN IF EXISTS organization_id")

    # Part 2: Drop teacher_limit
    op.execute("ALTER TABLE organizations DROP COLUMN IF EXISTS teacher_limit")

    # Part 1: Rollback soft delete strategy
    op.execute("DROP INDEX IF EXISTS idx_classroom_schools_is_active")
    op.execute("DROP INDEX IF EXISTS idx_teacher_schools_is_active")
    op.execute("DROP INDEX IF EXISTS idx_teacher_organizations_is_active")
    op.execute("DROP INDEX IF EXISTS idx_schools_is_active")
    op.execute("DROP INDEX IF EXISTS idx_organizations_is_active")
    op.execute("DROP INDEX IF EXISTS uq_teacher_org_owner")
    op.execute("DROP INDEX IF EXISTS uq_organizations_tax_id_active")

    # Restore tax_id unique constraint
    # WARNING: This will fail if there are duplicate tax_ids
    # Clean duplicates first if needed
    op.execute("""
        DO $$
        DECLARE
            dup_count INTEGER;
        BEGIN
            -- Check for duplicates
            SELECT COUNT(*) INTO dup_count
            FROM (
                SELECT tax_id, COUNT(*) as cnt
                FROM organizations
                WHERE tax_id IS NOT NULL
                GROUP BY tax_id
                HAVING COUNT(*) > 1
            ) AS dups;

            IF dup_count > 0 THEN
                -- Clean duplicates: Keep most recent, NULL others
                UPDATE organizations
                SET tax_id = NULL
                WHERE id IN (
                    SELECT id
                    FROM (
                        SELECT id,
                               ROW_NUMBER() OVER (
                                   PARTITION BY tax_id
                                   ORDER BY created_at DESC
                               ) as rn
                        FROM organizations
                        WHERE tax_id IS NOT NULL
                    ) AS ranked
                    WHERE rn > 1
                );
            END IF;

            -- Now safe to add unique constraint
            ALTER TABLE organizations
            ADD CONSTRAINT uq_organizations_tax_id UNIQUE (tax_id);
        END $$;
    """)
