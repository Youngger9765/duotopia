"""Create teacher_schools table

Missing table definition - required by permissions.py

Revision ID: 7f8g9h0i1j2k
Revises: 04221a3e73fc
Create Date: 2026-01-19 14:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "7f8e9d0c1b2a"
down_revision = "04221a3e73fc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create teacher_schools table

    This table stores teacher-school relationships with roles.
    Required by has_school_materials_permission() in utils/permissions.py

    Uses IF NOT EXISTS to handle both new and existing databases.
    """

    # Check if table exists before creating
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS teacher_schools (
            id SERIAL PRIMARY KEY,
            teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
            school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
            roles JSON NOT NULL DEFAULT '[]',
            permissions JSON,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE,
            CONSTRAINT uq_teacher_school UNIQUE (teacher_id, school_id)
        )
        """
    )

    # Create indexes (IF NOT EXISTS)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_teacher_schools_teacher_id ON teacher_schools(teacher_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_teacher_schools_school_id ON teacher_schools(school_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_teacher_schools_is_active ON teacher_schools(is_active)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_teacher_schools_active ON teacher_schools(teacher_id, school_id, is_active)"
    )


def downgrade() -> None:
    """
    Drop teacher_schools table and all indexes
    """

    op.drop_index("ix_teacher_schools_active", table_name="teacher_schools")
    op.drop_index("ix_teacher_schools_is_active", table_name="teacher_schools")
    op.drop_index("ix_teacher_schools_school_id", table_name="teacher_schools")
    op.drop_index("ix_teacher_schools_teacher_id", table_name="teacher_schools")
    op.drop_table("teacher_schools")
