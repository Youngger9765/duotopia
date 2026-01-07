"""add_distractors_column_to_content_items

Revision ID: 9a698a17a016
Revises: 549b3ef65c5e
Create Date: 2026-01-07 17:57:02.577534

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9a698a17a016"
down_revision: Union[str, None] = "549b3ef65c5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add distractors column to content_items table
    # This stores pre-generated distractor options for word selection practice
    # Format: ["干擾項1", "干擾項2", "干擾項3"]
    op.execute(
        """
        ALTER TABLE content_items
        ADD COLUMN IF NOT EXISTS distractors JSONB DEFAULT NULL
    """
    )


def downgrade() -> None:
    # Note: Using IF EXISTS for safety in shared DB environments
    op.execute(
        """
        ALTER TABLE content_items
        DROP COLUMN IF EXISTS distractors
    """
    )
