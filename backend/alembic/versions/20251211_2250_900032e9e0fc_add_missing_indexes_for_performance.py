"""add_missing_indexes_for_performance

Issue #94: Add missing database indexes to optimize slow queries

This migration adds indexes for frequently queried foreign keys:
- assignments.teacher_id (optimize teacher assignment queries)
- student_assignments.student_id (optimize student queries)
- student_assignments.assignment_id (optimize assignment queries)

Expected performance improvement: 10-50% on affected queries

Revision ID: 900032e9e0fc
Revises: cb0920d3ab63
Create Date: 2025-12-11 22:50:25.264374

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "900032e9e0fc"
down_revision: Union[str, None] = "cb0920d3ab63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing indexes for performance optimization"""
    # Add index on assignments.teacher_id to optimize teacher assignment queries
    op.create_index(
        "ix_assignments_teacher_id",
        "assignments",
        ["teacher_id"],
        unique=False,
        if_not_exists=True,
    )

    # Add index on student_assignments.student_id to optimize student queries
    op.create_index(
        "ix_student_assignments_student_id",
        "student_assignments",
        ["student_id"],
        unique=False,
        if_not_exists=True,
    )

    # Add index on student_assignments.assignment_id to optimize assignment queries
    op.create_index(
        "ix_student_assignments_assignment_id",
        "student_assignments",
        ["assignment_id"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    """Remove added indexes"""
    op.drop_index(
        "ix_student_assignments_assignment_id", table_name="student_assignments"
    )
    op.drop_index("ix_student_assignments_student_id", table_name="student_assignments")
    op.drop_index("ix_assignments_teacher_id", table_name="assignments")
