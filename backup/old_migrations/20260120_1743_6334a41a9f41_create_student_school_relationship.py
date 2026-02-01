"""create_student_school_relationship

Revision ID: 6334a41a9f41
Revises: 84e62a916eea
Create Date: 2026-01-20 17:43:55.335253

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6334a41a9f41'
down_revision: Union[str, None] = '84e62a916eea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create student_schools table
    op.create_table(
        'student_schools',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column(
            'enrolled_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=True
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'school_id', name='uq_student_school'),
    )
    
    # Create indexes
    op.create_index(
        'ix_student_schools_student_id',
        'student_schools',
        ['student_id'],
        unique=False
    )
    op.create_index(
        'ix_student_schools_school_id',
        'student_schools',
        ['school_id'],
        unique=False
    )
    op.create_index(
        'ix_student_schools_active',
        'student_schools',
        ['student_id', 'school_id', 'is_active'],
        unique=False
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_student_schools_active', table_name='student_schools')
    op.drop_index('ix_student_schools_school_id', table_name='student_schools')
    op.drop_index('ix_student_schools_student_id', table_name='student_schools')
    
    # Drop table
    op.drop_table('student_schools')
