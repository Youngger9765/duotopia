"""Add demo teacher account if not exists

Revision ID: 20260201_0306
Revises:
Create Date: 2026-02-01 03:06:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260201_0306"
down_revision = "g2b3c4d5e6f7"  # Previous: fix_auto_graded_historical_data
depends_on = None

# Demo account configuration
DEMO_EMAIL = "contact@duotopia.co"
DEMO_NAME = "Duotopia Demo"
# Password: DemoPass2026! (bcrypt hash)
DEMO_PASSWORD_HASH = "$2b$12$pyTz1WOVSBDCNadNuNKnxODOkRluKaC/kUJXZv/bGAuz.ea4LvcNi"


def upgrade():
    """Add demo teacher account if not exists (idempotent)"""
    # Use INSERT ... WHERE NOT EXISTS to ensure idempotency
    # This allows safe re-running on production where the account may already exist
    op.execute(
        f"""
        INSERT INTO teachers (email, password_hash, name, is_active, is_demo, created_at)
        SELECT
            '{DEMO_EMAIL}',
            '{DEMO_PASSWORD_HASH}',
            '{DEMO_NAME}',
            true,
            true,
            NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM teachers WHERE email = '{DEMO_EMAIL}'
        );
    """
    )


def downgrade():
    """Do not delete demo account - protect production data"""
    # We intentionally do not delete the demo account in downgrade
    # to prevent accidental data loss in production
    pass
