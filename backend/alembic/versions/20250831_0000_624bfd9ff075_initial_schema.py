"""Initial schema

Revision ID: 624bfd9ff075
Revises: 
Create Date: 2025-08-31 01:35:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '624bfd9ff075'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM types
    op.execute("CREATE TYPE programlevel AS ENUM ('BEGINNER', 'INTERMEDIATE', 'ADVANCED')")
    op.execute("CREATE TYPE contenttype AS ENUM ('reading_assessment', 'speaking_practice', 'speaking_scenario', 'listening_cloze', 'sentence_making', 'speaking_quiz')")
    op.execute("CREATE TYPE assignmentstatus AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'SUBMITTED', 'GRADED', 'RETURNED')")

    # Create teachers table
    op.create_table('teachers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_demo', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_teachers_email'), 'teachers', ['email'], unique=True)
    op.create_index(op.f('ix_teachers_id'), 'teachers', ['id'], unique=False)

    # Create students table
    op.create_table('students',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('student_id', sa.String(length=50), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('birthdate', sa.Date(), nullable=False),
        sa.Column('password_changed', sa.Boolean(), nullable=True),
        sa.Column('parent_email', sa.String(length=255), nullable=True),
        sa.Column('parent_phone', sa.String(length=20), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('target_wpm', sa.Integer(), nullable=True),
        sa.Column('target_accuracy', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_students_email'), 'students', ['email'], unique=True)
    op.create_index(op.f('ix_students_id'), 'students', ['id'], unique=False)

    # Create classrooms table
    op.create_table('classrooms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('grade', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('level', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_classrooms_id'), 'classrooms', ['id'], unique=False)

    # Create programs table
    op.create_table('programs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('level', postgresql.ENUM('BEGINNER', 'INTERMEDIATE', 'ADVANCED', name='programlevel', create_type=False), nullable=True),
        sa.Column('classroom_id', sa.Integer(), nullable=True),
        sa.Column('estimated_hours', sa.Float(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['classroom_id'], ['classrooms.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_programs_id'), 'programs', ['id'], unique=False)

    # Create lessons table
    op.create_table('lessons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('estimated_minutes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lessons_id'), 'lessons', ['id'], unique=False)

    # Create contents table
    op.create_table('contents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', postgresql.ENUM('reading_assessment', 'speaking_practice', 'speaking_scenario', 'listening_cloze', 'sentence_making', 'speaking_quiz', name='contenttype', create_type=False), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('items', sa.JSON(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('target_wpm', sa.Integer(), nullable=True),
        sa.Column('target_accuracy', sa.Float(), nullable=True),
        sa.Column('time_limit_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contents_id'), 'contents', ['id'], unique=False)

    # Create classroom_students table
    op.create_table('classroom_students',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('classroom_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['classroom_id'], ['classrooms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('classroom_id', 'student_id')
    )
    op.create_index(op.f('ix_classroom_students_id'), 'classroom_students', ['id'], unique=False)

    # Create student_assignments table
    op.create_table('student_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('classroom_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('status', postgresql.ENUM('NOT_STARTED', 'IN_PROGRESS', 'SUBMITTED', 'GRADED', 'RETURNED', name='assignmentstatus', create_type=False), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('graded_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['classroom_id'], ['classrooms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_student_assignments_id'), 'student_assignments', ['id'], unique=False)

    # Create assignment_submissions table
    op.create_table('assignment_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('submission_data', sa.JSON(), nullable=True),
        sa.Column('ai_feedback', sa.Text(), nullable=True),
        sa.Column('ai_scores', sa.JSON(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['assignment_id'], ['student_assignments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assignment_submissions_id'), 'assignment_submissions', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_index(op.f('ix_assignment_submissions_id'), table_name='assignment_submissions')
    op.drop_table('assignment_submissions')
    op.drop_index(op.f('ix_student_assignments_id'), table_name='student_assignments')
    op.drop_table('student_assignments')
    op.drop_index(op.f('ix_classroom_students_id'), table_name='classroom_students')
    op.drop_table('classroom_students')
    op.drop_index(op.f('ix_contents_id'), table_name='contents')
    op.drop_table('contents')
    op.drop_index(op.f('ix_lessons_id'), table_name='lessons')
    op.drop_table('lessons')
    op.drop_index(op.f('ix_programs_id'), table_name='programs')
    op.drop_table('programs')
    op.drop_index(op.f('ix_classrooms_id'), table_name='classrooms')
    op.drop_table('classrooms')
    op.drop_index(op.f('ix_students_id'), table_name='students')
    op.drop_index(op.f('ix_students_email'), table_name='students')
    op.drop_table('students')
    op.drop_index(op.f('ix_teachers_id'), table_name='teachers')
    op.drop_index(op.f('ix_teachers_email'), table_name='teachers')
    op.drop_table('teachers')
    
    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS assignmentstatus")
    op.execute("DROP TYPE IF EXISTS contenttype")
    op.execute("DROP TYPE IF EXISTS programlevel")