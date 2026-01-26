"""merge_orphaned_teacher_boolean_fix

Revision ID: a1b2c3d4e5f6
Revises: ed63e979dc1c, 808d3ca352c0
Create Date: 2026-01-20 08:02:00.000000

Fix: Merge orphaned migration ed63e979dc1c (fix_teacher_boolean_fields)
with main development line 808d3ca352c0 to ensure all migrations
including image_url column are applied.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = ("ed63e979dc1c", "808d3ca352c0")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
