"""Rename 30-Day Trial plan to Free Trial

Revision ID: 20260225_1000
Revises: 20260206_1000
Create Date: 2026-02-25 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260225_1000"
down_revision = "20260206_1000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename "30-Day Trial" to "Free Trial" in subscription_periods (idempotent)
    op.execute("""
        UPDATE subscription_periods
        SET plan_name = 'Free Trial'
        WHERE plan_name = '30-Day Trial'
    """)


def downgrade() -> None:
    op.execute("""
        UPDATE subscription_periods
        SET plan_name = '30-Day Trial'
        WHERE plan_name = 'Free Trial'
    """)
