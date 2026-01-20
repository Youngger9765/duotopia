"""fix_teacher_boolean_fields_null_values

Revision ID: ed63e979dc1c
Revises: 288ad5a75206
Create Date: 2026-01-01 02:57:24.355594

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ed63e979dc1c"
down_revision: Union[str, None] = "288ad5a75206"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update existing NULL values to False (must be done BEFORE adding NOT NULL constraint)
    op.execute(
        """
        UPDATE teachers
        SET is_demo = FALSE
        WHERE is_demo IS NULL
    """
    )

    op.execute(
        """
        UPDATE teachers
        SET is_admin = FALSE
        WHERE is_admin IS NULL
    """
    )

    # Add NOT NULL constraints with default values
    op.execute(
        """
        ALTER TABLE teachers
        ALTER COLUMN is_demo SET NOT NULL,
        ALTER COLUMN is_demo SET DEFAULT FALSE
    """
    )

    op.execute(
        """
        ALTER TABLE teachers
        ALTER COLUMN is_admin SET NOT NULL,
        ALTER COLUMN is_admin SET DEFAULT FALSE
    """
    )


def downgrade() -> None:
    # Remove NOT NULL constraints (allow NULL again)
    op.execute(
        """
        ALTER TABLE teachers
        ALTER COLUMN is_demo DROP NOT NULL,
        ALTER COLUMN is_admin DROP NOT NULL
    """
    )
