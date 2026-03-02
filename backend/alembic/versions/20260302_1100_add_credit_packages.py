"""Add credit_packages table and migrate Free Trial data

Revision ID: 20260302_1100
Revises: 20260302_1000
Create Date: 2026-03-02 11:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260302_1100"
down_revision = "20260302_1000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create credit_packages table (idempotent)
    op.execute("""
        CREATE TABLE IF NOT EXISTS credit_packages (
            id SERIAL PRIMARY KEY,
            teacher_id INTEGER REFERENCES teachers(id) ON DELETE CASCADE,
            organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
            package_id VARCHAR NOT NULL,
            points_total INTEGER NOT NULL,
            points_used INTEGER NOT NULL DEFAULT 0,
            price_paid INTEGER NOT NULL DEFAULT 0,
            purchased_at TIMESTAMPTZ NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'active',
            payment_id VARCHAR,
            source VARCHAR NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ
        )
    """)

    # 2. Create indexes (idempotent)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_credit_packages_teacher_status "
        "ON credit_packages (teacher_id, status)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_credit_packages_teacher_expires "
        "ON credit_packages (teacher_id, expires_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_credit_packages_org_status "
        "ON credit_packages (organization_id, status)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_credit_packages_expires_at "
        "ON credit_packages (expires_at)"
    )

    # 3. Migrate existing Free Trial SubscriptionPeriods to CreditPackages
    # Only migrate active Free Trial periods that haven't been migrated yet
    op.execute("""
        INSERT INTO credit_packages (
            teacher_id, package_id, points_total, points_used, price_paid,
            purchased_at, expires_at, status, source, created_at
        )
        SELECT
            sp.teacher_id,
            'trial-bonus',
            sp.quota_total,
            sp.quota_used,
            0,
            sp.start_date,
            sp.start_date + INTERVAL '1 year',
            'active',
            'trial_bonus',
            NOW()
        FROM subscription_periods sp
        WHERE sp.plan_name = 'Free Trial'
          AND sp.status = 'active'
          AND NOT EXISTS (
              SELECT 1 FROM credit_packages cp
              WHERE cp.teacher_id = sp.teacher_id
                AND cp.source = 'trial_bonus'
          )
    """)

    # 4. Mark migrated Free Trial SubscriptionPeriods
    op.execute("""
        UPDATE subscription_periods
        SET status = 'migrated'
        WHERE plan_name = 'Free Trial'
          AND status = 'active'
          AND teacher_id IN (
              SELECT teacher_id FROM credit_packages
              WHERE source = 'trial_bonus'
          )
    """)

    # 5. Make point_usage_logs.subscription_period_id nullable
    # (credit-package-only users won't have a subscription period)
    op.execute("""
        ALTER TABLE point_usage_logs
        ALTER COLUMN subscription_period_id DROP NOT NULL
    """)

    # 6. Add credit_package_id to point_usage_logs for tracking
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                          WHERE table_name = 'point_usage_logs'
                          AND column_name = 'credit_package_id') THEN
                ALTER TABLE point_usage_logs
                ADD COLUMN credit_package_id INTEGER
                REFERENCES credit_packages(id) ON DELETE SET NULL;
            END IF;
        END $$;
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_point_usage_logs_credit_package_id "
        "ON point_usage_logs (credit_package_id)"
    )


def downgrade() -> None:
    # Reverse: restore migrated Free Trial periods
    op.execute("""
        UPDATE subscription_periods
        SET status = 'active'
        WHERE plan_name = 'Free Trial'
          AND status = 'migrated'
    """)

    # Remove migrated trial bonus credit packages
    op.execute("""
        DELETE FROM credit_packages WHERE source = 'trial_bonus'
    """)

    op.execute("DROP TABLE IF EXISTS credit_packages")
