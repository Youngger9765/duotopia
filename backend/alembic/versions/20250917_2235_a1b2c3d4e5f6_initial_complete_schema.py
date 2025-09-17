"""Initial complete schema

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2025-09-17 22:35:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create all tables in correct order (respecting foreign key dependencies)

    # 1. Teachers table
    op.create_table(
        "teachers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True, default=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_teachers_email", "teachers", ["email"], unique=True)
    op.create_index("ix_teachers_id", "teachers", ["id"], unique=False)

    # 2. Students table
    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("student_number", sa.String(50), nullable=False),
        sa.Column("birthdate", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True, default=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_students_email", "students", ["email"], unique=True)
    op.create_index("ix_students_id", "students", ["id"], unique=False)
    op.create_index(
        "ix_students_student_number", "students", ["student_number"], unique=True
    )

    # 3. Programs table
    op.create_table(
        "programs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column(
            "level",
            sa.Enum("PREA", "A1", "A2", "B1", "B2", "C1", "C2", name="programlevel"),
            nullable=True,
        ),
        sa.Column("is_public", sa.Boolean(), nullable=True, default=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["teacher_id"],
            ["teachers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_programs_id", "programs", ["id"], unique=False)

    # 4. Lessons table
    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("program_id", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=True, default=0),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lessons_id", "lessons", ["id"], unique=False)

    # 5. Contents table (without items JSONB field)
    op.create_table(
        "contents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "READING_ASSESSMENT",
                "WRITING",
                "VOCABULARY",
                "LISTENING",
                name="contenttype",
            ),
            nullable=True,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=True, default=0),
        sa.Column("is_active", sa.Boolean(), nullable=True, default=True),
        sa.Column("target_wpm", sa.Integer(), nullable=True),
        sa.Column("target_accuracy", sa.Float(), nullable=True),
        sa.Column("time_limit_seconds", sa.Integer(), nullable=True),
        sa.Column("level", sa.String(10), nullable=True, default="A1"),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=True, default=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["lesson_id"],
            ["lessons.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contents_id", "contents", ["id"], unique=False)

    # 6. ContentItems table
    op.create_table(
        "content_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("content_id", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("translation", sa.Text(), nullable=True),
        sa.Column("audio_url", sa.Text(), nullable=True),
        sa.Column(
            "item_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["content_id"], ["contents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_content_items_content_id", "content_items", ["content_id"], unique=False
    )
    op.create_index("ix_content_items_id", "content_items", ["id"], unique=False)

    # 7. Classrooms table
    op.create_table(
        "classrooms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("grade", sa.String(20), nullable=True),
        sa.Column("school", sa.String(100), nullable=True),
        sa.Column("academic_year", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, default=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["teacher_id"],
            ["teachers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_classrooms_id", "classrooms", ["id"], unique=False)

    # 8. ClassroomStudents table
    op.create_table(
        "classroom_students",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("classroom_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["classroom_id"], ["classrooms.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "classroom_id", "student_id", name="unique_classroom_student"
        ),
    )
    op.create_index(
        "ix_classroom_students_id", "classroom_students", ["id"], unique=False
    )

    # 9. Assignments table
    op.create_table(
        "assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("classroom_id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("DRAFT", "PUBLISHED", "CLOSED", name="assignmentstatus"),
            nullable=True,
            default="PUBLISHED",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=True, default=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["classroom_id"],
            ["classrooms.id"],
        ),
        sa.ForeignKeyConstraint(
            ["teacher_id"],
            ["teachers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assignments_id", "assignments", ["id"], unique=False)

    # 10. AssignmentContents table
    op.create_table(
        "assignment_contents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column("content_id", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=True, default=0),
        sa.ForeignKeyConstraint(
            ["assignment_id"], ["assignments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["content_id"], ["contents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "assignment_id", "content_id", name="unique_assignment_content"
        ),
    )
    op.create_index(
        "ix_assignment_contents_id", "assignment_contents", ["id"], unique=False
    )

    # 11. StudentAssignments table
    op.create_table(
        "student_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assignment_id", sa.Integer(), nullable=True),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("classroom_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "NOT_STARTED",
                "IN_PROGRESS",
                "SUBMITTED",
                "GRADED",
                "RETURNED",
                "COMPLETED",
                name="assignmentstatus",
            ),
            nullable=True,
            default="NOT_STARTED",
        ),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, default=True),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("graded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["assignments.id"],
        ),
        sa.ForeignKeyConstraint(
            ["classroom_id"],
            ["classrooms.id"],
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["students.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_student_assignments_id", "student_assignments", ["id"], unique=False
    )

    # 12. StudentContentProgress table
    op.create_table(
        "student_content_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_assignment_id", sa.Integer(), nullable=False),
        sa.Column("content_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "NOT_STARTED",
                "IN_PROGRESS",
                "SUBMITTED",
                "GRADED",
                "RETURNED",
                "COMPLETED",
                name="assignmentstatus",
            ),
            nullable=True,
            default="NOT_STARTED",
        ),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=True, default=0),
        sa.Column("is_locked", sa.Boolean(), nullable=True, default=False),
        sa.Column("checked", sa.Boolean(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column(
            "response_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("ai_scores", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_spent_seconds", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["content_id"],
            ["contents.id"],
        ),
        sa.ForeignKeyConstraint(
            ["student_assignment_id"],
            ["student_assignments.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_student_content_progress_id",
        "student_content_progress",
        ["id"],
        unique=False,
    )

    # 13. StudentItemProgress table
    op.create_table(
        "student_item_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_assignment_id", sa.Integer(), nullable=False),
        sa.Column("content_item_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "NOT_STARTED",
                "IN_PROGRESS",
                "SUBMITTED",
                "GRADED",
                "RETURNED",
                "COMPLETED",
                name="assignmentstatus",
            ),
            nullable=True,
            default="NOT_STARTED",
        ),
        sa.Column("recording_url", sa.Text(), nullable=True),
        sa.Column("transcription", sa.Text(), nullable=True),
        sa.Column("accuracy_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("fluency_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("pronunciation_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("completeness_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("prosody_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("ai_feedback", sa.Text(), nullable=True),
        sa.Column(
            "response_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ai_assessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["content_item_id"],
            ["content_items.id"],
        ),
        sa.ForeignKeyConstraint(
            ["student_assignment_id"],
            ["student_assignments.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "student_assignment_id",
            "content_item_id",
            name="unique_student_item_progress",
        ),
    )
    op.create_index(
        "ix_student_item_progress_id", "student_item_progress", ["id"], unique=False
    )


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_index("ix_student_item_progress_id", table_name="student_item_progress")
    op.drop_table("student_item_progress")

    op.drop_index(
        "ix_student_content_progress_id", table_name="student_content_progress"
    )
    op.drop_table("student_content_progress")

    op.drop_index("ix_student_assignments_id", table_name="student_assignments")
    op.drop_table("student_assignments")

    op.drop_index("ix_assignment_contents_id", table_name="assignment_contents")
    op.drop_table("assignment_contents")

    op.drop_index("ix_assignments_id", table_name="assignments")
    op.drop_table("assignments")

    op.drop_index("ix_classroom_students_id", table_name="classroom_students")
    op.drop_table("classroom_students")

    op.drop_index("ix_classrooms_id", table_name="classrooms")
    op.drop_table("classrooms")

    op.drop_index("ix_content_items_id", table_name="content_items")
    op.drop_index("ix_content_items_content_id", table_name="content_items")
    op.drop_table("content_items")

    op.drop_index("ix_contents_id", table_name="contents")
    op.drop_table("contents")

    op.drop_index("ix_lessons_id", table_name="lessons")
    op.drop_table("lessons")

    op.drop_index("ix_programs_id", table_name="programs")
    op.drop_table("programs")

    op.drop_index("ix_students_student_number", table_name="students")
    op.drop_index("ix_students_id", table_name="students")
    op.drop_index("ix_students_email", table_name="students")
    op.drop_table("students")

    op.drop_index("ix_teachers_id", table_name="teachers")
    op.drop_index("ix_teachers_email", table_name="teachers")
    op.drop_table("teachers")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS assignmentstatus")
    op.execute("DROP TYPE IF EXISTS contenttype")
    op.execute("DROP TYPE IF EXISTS programlevel")
