"""add_subscription_dates_to_organization

Revision ID: 238cc2af0367
Revises: 7d39900cc008
Create Date: 2026-02-03 14:28:09.315344

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "238cc2af0367"
down_revision: Union[str, None] = "20260203_0143"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add subscription_start_date column (idempotent)
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'organizations' AND column_name = 'subscription_start_date'
            ) THEN
                ALTER TABLE organizations ADD COLUMN subscription_start_date TIMESTAMP WITH TIME ZONE;
            END IF;
        END $$;
    """
    )

    # Add subscription_end_date column (idempotent)
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'organizations' AND column_name = 'subscription_end_date'
            ) THEN
                ALTER TABLE organizations ADD COLUMN subscription_end_date TIMESTAMP WITH TIME ZONE;
            END IF;
        END $$;
    """
    )


def downgrade() -> None:
    # Remove subscription_end_date if exists
    op.execute(
        """
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'organizations' AND column_name = 'subscription_end_date'
            ) THEN
                ALTER TABLE organizations DROP COLUMN subscription_end_date;
            END IF;
        END $$;
    """
    )

    # Remove subscription_start_date if exists
    op.execute(
        """
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'organizations' AND column_name = 'subscription_start_date'
            ) THEN
                ALTER TABLE organizations DROP COLUMN subscription_start_date;
            END IF;
        END $$;
    """
    )
