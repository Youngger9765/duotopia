"""add_organization_performance_indexes

Revision ID: 16ea1d78b460
Revises: 5106b545b6d2
Create Date: 2025-11-29 16:39:10.508541

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "16ea1d78b460"
down_revision: Union[str, None] = "5106b545b6d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing permissions column to teacher_schools
    # Use JSONB for PostgreSQL (better performance with GIN indexes)
    if op.get_bind().dialect.name == "postgresql":
        with op.batch_alter_table("teacher_schools", schema=None) as batch_op:
            batch_op.add_column(
                sa.Column("permissions", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
            )
    else:
        # Use JSON for SQLite compatibility
        with op.batch_alter_table("teacher_schools", schema=None) as batch_op:
            batch_op.add_column(sa.Column("permissions", sa.JSON(), nullable=True))

    # Create GIN indexes for JSONB columns in teacher_schools (PostgreSQL only)
    # GIN indexes are optimal for JSONB queries (containment, existence checks)
    # Skip for SQLite as it doesn't support GIN indexes
    if op.get_bind().dialect.name == "postgresql":
        op.create_index(
            "ix_teacher_schools_roles_gin",
            "teacher_schools",
            ["roles"],
            unique=False,
            postgresql_using="gin",
            postgresql_ops={"roles": "jsonb_path_ops"},
        )

        op.create_index(
            "ix_teacher_schools_permissions_gin",
            "teacher_schools",
            ["permissions"],
            unique=False,
            postgresql_using="gin",
            postgresql_ops={"permissions": "jsonb_path_ops"},
        )

    # Create composite index for common query patterns
    # This helps with queries filtering by teacher and organization together
    op.create_index(
        "ix_teacher_organizations_composite",
        "teacher_organizations",
        ["teacher_id", "organization_id"],
        unique=False,
    )

    # Create composite index for teacher-school queries
    op.create_index(
        "ix_teacher_schools_composite",
        "teacher_schools",
        ["teacher_id", "school_id"],
        unique=False,
    )

    # Create composite index for classroom-school queries
    op.create_index(
        "ix_classroom_schools_composite",
        "classroom_schools",
        ["classroom_id", "school_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop composite indexes
    op.drop_index("ix_classroom_schools_composite", table_name="classroom_schools")
    op.drop_index("ix_teacher_schools_composite", table_name="teacher_schools")
    op.drop_index(
        "ix_teacher_organizations_composite", table_name="teacher_organizations"
    )

    # Drop GIN indexes (PostgreSQL only)
    if op.get_bind().dialect.name == "postgresql":
        op.drop_index(
            "ix_teacher_schools_permissions_gin", table_name="teacher_schools"
        )
        op.drop_index("ix_teacher_schools_roles_gin", table_name="teacher_schools")

    # Drop permissions column
    with op.batch_alter_table("teacher_schools", schema=None) as batch_op:
        batch_op.drop_column("permissions")
