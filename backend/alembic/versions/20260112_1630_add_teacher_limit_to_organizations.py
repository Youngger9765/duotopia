"""Add teacher_limit column to organizations

Per #151 spec decision #5: Teacher Authorization Count
- Add teacher_limit field to track organization's teacher quota
- Nullable to support organizations without limit

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-12 16:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add teacher_limit column to organizations table.

    Decision #5: Teacher authorization count logic
    - teacher_limit is nullable (no limit if NULL)
    - Default to NULL (unlimited)
    - Can be set during organization creation or update
    """

    op.add_column(
        "organizations",
        sa.Column("teacher_limit", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """
    Remove teacher_limit column.
    """

    op.drop_column("organizations", "teacher_limit")
