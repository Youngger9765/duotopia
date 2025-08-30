"""complete initial schema with all fields

Revision ID: 13ed6b11e858
Revises: 
Create Date: 2025-08-31 01:01:34.329151

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '13ed6b11e858'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create teachers table
    op.create_table('teachers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('school_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create students table
    op.create_table('students',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('nickname', sa.String(), nullable=True),
        sa.Column('school_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create classrooms table
    op.create_table('classrooms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create programs table
    op.create_table('programs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.JSON(), nullable=False),
        sa.Column('description', sa.JSON(), nullable=True),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('is_published', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create lessons table
    op.create_table('lessons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('name', sa.JSON(), nullable=False),
        sa.Column('description', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create contents table WITH level and tags fields!
    op.create_table('contents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.JSON(), nullable=False),
        sa.Column('activity_data', sa.JSON(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('level', sa.String(length=10), nullable=True, server_default='A1'),
        sa.Column('tags', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create student_assignments table
    op.create_table('student_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('assigned_by', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_by'], ['teachers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create assignment_submissions table
    op.create_table('assignment_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('submission_data', sa.JSON(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('ai_feedback', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['assignment_id'], ['student_assignments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create classroom_students table
    op.create_table('classroom_students',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('classroom_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['classroom_id'], ['classrooms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('classroom_id', 'student_id')
    )
    
    # Create indexes
    op.create_index('idx_student_email', 'students', ['email'])
    op.create_index('idx_teacher_email', 'teachers', ['email'])
    op.create_index('idx_classroom_teacher', 'classrooms', ['teacher_id'])
    op.create_index('idx_student_assignment', 'student_assignments', ['student_id', 'content_id'])


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_index('idx_student_assignment')
    op.drop_index('idx_classroom_teacher')
    op.drop_index('idx_teacher_email')
    op.drop_index('idx_student_email')
    
    op.drop_table('classroom_students')
    op.drop_table('assignment_submissions')
    op.drop_table('student_assignments')
    op.drop_table('contents')
    op.drop_table('lessons')
    op.drop_table('programs')
    op.drop_table('classrooms')
    op.drop_table('students')
    op.drop_table('teachers')