"""add_completeness_score_to_student_item_progress

Revision ID: 288ad5a75206
Revises: cd6eab4e2001
Create Date: 2025-12-02 16:46:22.176819

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "288ad5a75206"
down_revision: Union[str, None] = "cd6eab4e2001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add completeness_score field to student_item_progress table
    op.add_column(
        "student_item_progress",
        sa.Column("completeness_score", sa.DECIMAL(5, 2), nullable=True),
    )


def downgrade() -> None:
    # Remove completeness_score field from student_item_progress table
    op.drop_column("student_item_progress", "completeness_score")
