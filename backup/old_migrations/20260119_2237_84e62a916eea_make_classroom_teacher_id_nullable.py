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
    # Check for NULL teacher_id values before enforcing non-null constraint
    connection = op.get_bind()
    result = connection.execute(
        sa.text("SELECT COUNT(*) FROM classrooms WHERE teacher_id IS NULL")
    )
    count = result.scalar()

    if count > 0:
        raise Exception(
            f"Cannot downgrade: {count} classrooms have NULL teacher_id. "
            "Please assign teachers to these classrooms before downgrading."
        )

    # Safe to make non-nullable since we verified no NULL values exist
    op.alter_column('classrooms', 'teacher_id',
                    existing_type=sa.INTEGER(),
                    nullable=False)
