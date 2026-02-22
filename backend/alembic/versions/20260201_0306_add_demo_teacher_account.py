"""Add demo teacher account if not exists

Revision ID: 20260201_0306
Revises:
Create Date: 2026-02-01 03:06:00.000000

"""
import os
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "20260201_0306"
down_revision = "g2b3c4d5e6f7"  # Previous: fix_auto_graded_historical_data
depends_on = None

# Demo account configuration
DEMO_EMAIL = "contact@duotopia.co"
DEMO_NAME = "Duotopia Demo"


def upgrade():
    """Add demo teacher account if not exists (idempotent)"""
    # Password hash is read from environment variable to avoid storing secrets in code
    password_hash = os.environ.get("DEMO_PASSWORD_HASH", "")
    if not password_hash:
        # Skip if env var not set (e.g. in test environments)
        return

    # Use parameterized query to prevent SQL injection
    op.execute(
        text(
            """
            INSERT INTO teachers (email, password_hash, name, is_active, is_demo, created_at)
            SELECT
                :email,
                :password_hash,
                :name,
                true,
                true,
                NOW()
            WHERE NOT EXISTS (
                SELECT 1 FROM teachers WHERE email = :email
            );
        """
        ),
        {"email": DEMO_EMAIL, "password_hash": password_hash, "name": DEMO_NAME},
    )


def downgrade():
    """Do not delete demo account - protect production data"""
    # We intentionally do not delete the demo account in downgrade
    # to prevent accidental data loss in production
    pass
