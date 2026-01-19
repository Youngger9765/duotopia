"""make classroom teacher_id nullable

Revision ID: 84e62a916eea
Revises: 04221a3e73fc
Create Date: 2026-01-19 22:37:09.561159

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '84e62a916eea'
down_revision: Union[str, None] = '04221a3e73fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make classroom teacher_id nullable to allow school admin creation before teacher assignment
    op.alter_column('classrooms', 'teacher_id',
                    existing_type=sa.INTEGER(),
                    nullable=True)


def downgrade() -> None:
    # Revert teacher_id to non-nullable
    # WARNING: This will fail if there are classrooms with NULL teacher_id
    op.alter_column('classrooms', 'teacher_id',
                    existing_type=sa.INTEGER(),
                    nullable=False)
