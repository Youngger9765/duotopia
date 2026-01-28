# Issue #112 Migration Squash Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Consolidate 7 migrations from feat/issue-112 into a single migration for staging

**Architecture:** Safe migration squashing strategy that works with already-applied migrations in staging DB

**Tech Stack:** Alembic, PostgreSQL, Python 3.11

**Context:**
- Issue #112 created 7 separate migration files
- Staging DB already has these migrations applied
- We need to consolidate into 1 migration for staging branch
- Must be idempotent (can run safely even if DB already has changes)

---

## Current State Analysis

### Staging Branch
- Last migration: `20260111_1217_d21f6f58c952_merge_multiple_heads.py`
- Total migrations: 20 files

### Issue #112 Branch (7 New Migrations)

1. **20260112_1600** - Soft delete strategy
   - Drop tax_id unique constraint
   - Add tax_id partial unique index (is_active=true)
   - Add org_owner unique constraint
   - Add is_active indexes (organizations, schools, teacher_organizations, teacher_schools, classroom_schools)

2. **20260112_1630** - Teacher limit
   - Add `organizations.teacher_limit` column (nullable int)

3. **20260114_1527** - Organization ID to programs
   - Add `programs.organization_id` column (UUID, nullable)
   - Add FK constraint to organizations
   - Data migration: Extract from source_metadata JSON

4. **20260115_0826** - Content types enum
   - Add enum values: example_sentences, vocabulary_set, single_choice_quiz, scenario_dialogue

5. **20260115_1557** - School ID to programs
   - Add `programs.school_id` column (UUID, nullable)
   - Add FK constraint to schools

6. **20260119_2237** - Classroom teacher nullable
   - Make `classrooms.teacher_id` nullable

7. **20260120_1743** - Student schools table
   - Create `student_schools` table with columns: id, student_id, school_id, is_active, enrolled_at, created_at, updated_at
   - Add FK constraints and indexes

---

## Strategy: Safe Squash with IF NOT EXISTS

**Why this approach:**
- Staging DB already has these changes applied
- We can't drop and recreate (data loss risk)
- Solution: Use IF NOT EXISTS / IF EXISTS for all operations
- Result: Idempotent migration that can run safely multiple times

**Workflow:**
1. Merge staging into feat/issue-112 (get latest staging code)
2. Create new consolidated migration in feat/issue-112
3. Mark old migrations as "already applied" (stamp)
4. Test in #112 environment
5. Cherry-pick consolidated migration to staging

---

## Task 1: Merge Staging into Issue #112

**Files:**
- Modify: feat/issue-112 branch (git merge)

**Step 1: Fetch latest staging**

```bash
git fetch origin staging
```

**Step 2: Merge staging into current branch**

```bash
git merge origin/staging
```

Expected: May have merge conflicts in migration files or alembic chain

**Step 3: Resolve conflicts (if any)**

Priority order:
1. Keep staging's migration files intact
2. Append #112's migrations after staging's last migration
3. Update down_revision pointers if needed

**Step 4: Verify merge**

```bash
git log --oneline --graph origin/staging..HEAD | head -20
```

Expected: Clean merge history showing staging commits integrated

**Step 5: Commit merge**

```bash
git commit -m "chore: merge staging to resolve migration base"
```

---

## Task 2: Create Consolidated Migration

**Files:**
- Create: `backend/alembic/versions/20260125_squashed_organization_hierarchy.py`

**Step 1: Create new migration file**

Create file: `backend/alembic/versions/20260125_add_organization_student_management.py`

```python
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
```

**Step 2: Verify migration file syntax**

```bash
python -m py_compile backend/alembic/versions/20260125_add_organization_student_management.py
```

Expected: No syntax errors

**Step 3: Commit new migration**

```bash
git add backend/alembic/versions/20260125_add_organization_student_management.py
git commit -m "feat(migration): add organization hierarchy and student management schema

Consolidates:
- Soft delete strategy with partial indexes
- Teacher limit column
- Organization/school ID to programs
- Content types enum expansion
- Classroom teacher nullable
- Student schools relationship table

All operations are idempotent using IF NOT EXISTS."
```

---

## Task 3: Mark Old Migrations as Applied

**Files:**
- None (DB operation only)

**Step 1: Connect to staging DB**

Get staging DB connection string from environment or .env file.

**Step 2: Mark old migrations as "already applied"**

Since we're consolidating 7 migrations into 1, we need to tell Alembic that those old migrations are already applied (skip them).

**Option A: Use alembic stamp (safer)**

```bash
# This tells Alembic: "Treat these migrations as already applied"
# without actually running them

# First, check current DB revision
alembic current

# Stamp the new consolidated migration
alembic stamp add_org_student_mgmt
```

**Option B: Delete old migration files**

After confirming consolidated migration works:

```bash
# Backup first
mkdir -p backup/old_migrations
mv backend/alembic/versions/20260112_1600_*.py backup/old_migrations/
mv backend/alembic/versions/20260112_1630_*.py backup/old_migrations/
mv backend/alembic/versions/20260114_1527_*.py backup/old_migrations/
mv backend/alembic/versions/20260115_0826_*.py backup/old_migrations/
mv backend/alembic/versions/20260115_1557_*.py backup/old_migrations/
mv backend/alembic/versions/20260119_2237_*.py backup/old_migrations/
mv backend/alembic/versions/20260120_1743_*.py backup/old_migrations/
```

**Step 3: Commit deletion**

```bash
git add backend/alembic/versions/
git commit -m "chore(migration): remove old migrations replaced by consolidated migration"
```

---

## Task 4: Test Migration in Issue #112 Environment

**Files:**
- None (testing only)

**Step 1: Deploy to #112 test environment**

Trigger GitHub Actions workflow for PR #112 deployment.

**Step 2: Check deployment logs**

Look for migration execution:
```
INFO [alembic.runtime.migration] Running upgrade ... -> add_org_student_mgmt
```

Expected outcomes:
- ✅ **If DB already has changes:** Migration completes with "already exists" notices (idempotent)
- ✅ **If DB is fresh:** Migration creates all schema changes
- ❌ **If fails:** Check error logs, fix migration, redeploy

**Step 3: Verify schema changes**

Connect to #112 test database:

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables
WHERE table_name IN ('student_schools', 'organizations', 'programs');

-- Check columns exist
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'organizations'
AND column_name IN ('teacher_limit', 'tax_id');

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'programs'
AND column_name IN ('organization_id', 'school_id');

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'classrooms'
AND column_name = 'teacher_id';

-- Check indexes exist
SELECT indexname FROM pg_indexes
WHERE tablename = 'organizations'
AND indexname LIKE '%is_active%';

SELECT indexname FROM pg_indexes
WHERE tablename = 'student_schools';

-- Check enum values
SELECT enumlabel FROM pg_enum
WHERE enumtypid = 'contenttype'::regtype
AND enumlabel IN ('example_sentences', 'vocabulary_set', 'single_choice_quiz', 'scenario_dialogue');
```

Expected: All schema changes present

**Step 4: Test application endpoints**

Run API tests that use the new schema:

```bash
# From project root
npm run test:api:organizations
npm run test:api:programs
npm run test:api:students
```

Expected: All tests pass

**Step 5: Commit test results**

Document in PR comments or Slack:
```
✅ Migration add_org_student_mgmt tested successfully
- Deployed to issue-112 test environment
- Schema verified: all tables/columns/indexes present
- API tests passed
- Ready for cherry-pick to staging
```

---

## Task 5: Cherry-Pick to Staging

**Files:**
- Modify: staging branch

**Step 1: Switch to staging branch**

```bash
git checkout staging
git pull origin staging
```

**Step 2: Cherry-pick the consolidated migration commit**

```bash
# Find the commit hash for the new migration
git log feat/issue-112 --oneline | grep "add_organization_student_management"

# Cherry-pick it
git cherry-pick <commit-hash>
```

Expected: Clean cherry-pick (no conflicts)

**Step 3: Verify staging branch state**

```bash
# Check migration files
ls -la backend/alembic/versions/ | tail -5

# Should see:
# 20260111_1217_d21f6f58c952_merge_multiple_heads.py
# 20260125_add_organization_student_management.py

# Check migration chain
alembic history | head -5
```

Expected: Clean migration chain from staging's last migration to new squashed migration

**Step 4: Push to staging**

```bash
git push origin staging
```

**Step 5: Monitor staging deployment**

```bash
# Watch GitHub Actions
gh run list --branch staging --limit 1

# Wait for completion
gh run watch <run-id>
```

Expected outcomes:
- ✅ Staging backend deploys successfully
- ✅ Migration runs (or skips if already applied)
- ✅ All tests pass

**Step 6: Verify staging database**

Same verification queries as Task 4 Step 3, but against staging database.

**Step 7: Update Issue #112**

Comment on issue:
```
✅ Migration consolidation complete

Consolidated 7 migrations into 1:
- backend/alembic/versions/20260125_add_organization_student_management.py

Changes deployed to staging:
- Staging DB schema updated
- All tests passing
- Other per-issue environments can now deploy successfully

Next: Merge #112 PR to staging
```

---

## Task 6: Update Project Documentation

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Document migration incident**

Add to `.claude/learning/migration-incident-2026-01-25.json`:

```json
{
  "incident_date": "2026-01-25",
  "type": "migration_conflict",
  "root_cause": "Created migrations in feature branch instead of staging",
  "impact": "Other per-issue environments failed to deploy (Alembic revision mismatch)",
  "resolution": "Consolidated 7 migrations into 1, cherry-picked to staging",
  "lesson": "Always create migrations in staging branch first for shared DB architectures",
  "prevention": "Updated CLAUDE.md with mandatory workflow, added pre-flight hook"
}
```

**Step 2: Reinforce migration rules in CLAUDE.md**

Verify these rules exist (already documented):

```markdown
### 🚨 Database Migration Rules (CRITICAL)

**Migration Creation Workflow:**

1. ❌ **NEVER** create migrations in feature branches
2. ✅ **ALWAYS** create migrations in staging branch first
3. ⚠️ **ASK** before creating any migration
```

**Step 3: Commit documentation**

```bash
git add .claude/learning/migration-incident-2026-01-25.json
git commit -m "docs: document migration consolidation incident and resolution"
```

---

## Verification Checklist

Before marking complete, verify:

- [ ] All 7 old migration files removed from feat/issue-112
- [ ] New consolidated migration file created
- [ ] Migration tested in #112 environment (passes)
- [ ] Migration cherry-picked to staging
- [ ] Staging deployment successful
- [ ] Staging database schema verified
- [ ] All per-issue environments can now deploy
- [ ] Documentation updated
- [ ] Team notified in Slack

---

## Rollback Plan

If consolidated migration fails in staging:

**Option 1: Revert cherry-pick**

```bash
git checkout staging
git revert <cherry-pick-commit-hash>
git push origin staging
```

**Option 2: Downgrade database**

```bash
alembic downgrade d21f6f58c952  # Revert to staging's last migration
```

**Option 3: Emergency fix**

If migration has bugs:
1. Fix in feat/issue-112
2. Test in #112 environment
3. Cherry-pick fix to staging
4. Redeploy

---

## Success Criteria

Migration consolidation is complete when:

1. ✅ Staging branch has exactly 1 new migration (not 7)
2. ✅ Staging DB schema matches #112 DB schema
3. ✅ Other per-issue environments deploy successfully
4. ✅ All tests pass in both #112 and staging
5. ✅ Team understands new migration workflow

**Estimated effort:** 2-3 hours (including testing and verification)

**Risk level:** 🟡 Medium (DB operations always risky, but we have rollback plan)
