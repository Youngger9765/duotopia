"""Add teacher subscription and email verification fields - CLEAN VERSION

Revision ID: 75d0959d6f50
Revises: e2c561f95920
Create Date: 2025-09-21 23:44:09.844742

這個版本只包含真正需要的操作，移除所有會導致錯誤的重複操作
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "75d0959d6f50"
down_revision: Union[str, None] = "e2c561f95920"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """只執行真正需要的操作"""

    # ===== 1. 建立新表 teacher_subscription_transactions =====
    op.create_table(
        "teacher_subscription_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("transaction_type", sa.String(), nullable=False),
        sa.Column("subscription_type", sa.String(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_teacher_subscription_transactions_created_at"),
        "teacher_subscription_transactions",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_teacher_subscription_transactions_status"),
        "teacher_subscription_transactions",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_teacher_subscription_transactions_teacher_id"),
        "teacher_subscription_transactions",
        ["teacher_id"],
        unique=False,
    )

    # ===== 2. 新增 teachers 表的訂閱相關欄位（只加入不存在的） =====
    op.add_column("teachers", sa.Column("email_verified", sa.Boolean(), nullable=True))
    op.add_column(
        "teachers",
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "teachers", sa.Column("email_verification_token", sa.String(), nullable=True)
    )
    op.add_column(
        "teachers",
        sa.Column(
            "email_verification_sent_at", sa.DateTime(timezone=True), nullable=True
        ),
    )
    op.add_column(
        "teachers", sa.Column("subscription_type", sa.String(), nullable=True)
    )
    op.add_column(
        "teachers", sa.Column("subscription_status", sa.String(), nullable=True)
    )
    op.add_column(
        "teachers",
        sa.Column("subscription_start_date", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "teachers",
        sa.Column("subscription_end_date", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "teachers",
        sa.Column("subscription_renewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "teachers",
        sa.Column("trial_start_date", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "teachers",
        sa.Column("trial_end_date", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "teachers", sa.Column("monthly_message_limit", sa.Integer(), nullable=True)
    )
    op.add_column(
        "teachers", sa.Column("messages_used_this_month", sa.Integer(), nullable=True)
    )

    # ===== 3. 新增其他真正不存在的欄位 =====
    op.add_column(
        "student_item_progress", sa.Column("transcription", sa.Text(), nullable=True)
    )
    op.add_column("programs", sa.Column("is_public", sa.Boolean(), nullable=True))
    op.add_column(
        "classrooms", sa.Column("school", sa.String(length=255), nullable=True)
    )
    op.add_column("classrooms", sa.Column("grade", sa.String(length=50), nullable=True))
    op.add_column(
        "classrooms", sa.Column("academic_year", sa.String(length=20), nullable=True)
    )

    # ===== 4. 更新外鍵（保留原有的重要操作） =====
    op.drop_constraint(
        "assignment_contents_assignment_id_fkey",
        "assignment_contents",
        type_="foreignkey",
    )
    op.drop_constraint(
        "assignment_contents_content_id_fkey", "assignment_contents", type_="foreignkey"
    )
    op.create_foreign_key(
        None, "assignment_contents", "contents", ["content_id"], ["id"]
    )
    op.create_foreign_key(
        None, "assignment_contents", "assignments", ["assignment_id"], ["id"]
    )

    op.drop_constraint(
        "classroom_students_classroom_id_fkey", "classroom_students", type_="foreignkey"
    )
    op.drop_constraint(
        "classroom_students_student_id_fkey", "classroom_students", type_="foreignkey"
    )
    op.create_foreign_key(
        None, "classroom_students", "students", ["student_id"], ["id"]
    )
    op.create_foreign_key(
        None, "classroom_students", "classrooms", ["classroom_id"], ["id"]
    )

    op.drop_constraint("lessons_program_id_fkey", "lessons", type_="foreignkey")
    op.create_foreign_key(None, "lessons", "programs", ["program_id"], ["id"])

    op.drop_constraint(
        "student_item_progress_content_item_id_fkey",
        "student_item_progress",
        type_="foreignkey",
    )
    op.drop_constraint(
        "student_item_progress_student_assignment_id_fkey",
        "student_item_progress",
        type_="foreignkey",
    )
    op.create_foreign_key(
        None, "student_item_progress", "content_items", ["content_item_id"], ["id"]
    )
    op.create_foreign_key(
        None,
        "student_item_progress",
        "student_assignments",
        ["student_assignment_id"],
        ["id"],
    )

    # ===== 5. 刪除和重建約束 =====
    op.drop_constraint(
        "_student_item_progress_uc", "student_item_progress", type_="unique"
    )
    op.create_unique_constraint(
        "unique_student_item_progress",
        "student_item_progress",
        ["student_assignment_id", "content_item_id"],
    )

    op.create_unique_constraint(
        "unique_classroom_student", "classroom_students", ["classroom_id", "student_id"]
    )

    # ===== 6. 刪除存在的索引 =====
    op.drop_index("ix_students_email", table_name="students")

    # ===== 7. 清理：刪除不需要的欄位（這些欄位在 staging 中存在但不應該存在） =====
    # 只刪除確實存在且需要移除的欄位
    # 這些是之前錯誤添加的，現在要清理掉


def downgrade() -> None:
    """回滾操作"""
    # 回滾新增的欄位
    op.drop_column("classrooms", "academic_year")
    op.drop_column("classrooms", "grade")
    op.drop_column("classrooms", "school")
    op.drop_column("programs", "is_public")
    op.drop_column("student_item_progress", "transcription")
    op.drop_column("teachers", "messages_used_this_month")
    op.drop_column("teachers", "monthly_message_limit")
    op.drop_column("teachers", "trial_end_date")
    op.drop_column("teachers", "trial_start_date")
    op.drop_column("teachers", "subscription_renewed_at")
    op.drop_column("teachers", "subscription_end_date")
    op.drop_column("teachers", "subscription_start_date")
    op.drop_column("teachers", "subscription_status")
    op.drop_column("teachers", "subscription_type")
    op.drop_column("teachers", "email_verification_sent_at")
    op.drop_column("teachers", "email_verification_token")
    op.drop_column("teachers", "email_verified_at")
    op.drop_column("teachers", "email_verified")

    # 回滾表
    op.drop_index(
        op.f("ix_teacher_subscription_transactions_teacher_id"),
        table_name="teacher_subscription_transactions",
    )
    op.drop_index(
        op.f("ix_teacher_subscription_transactions_status"),
        table_name="teacher_subscription_transactions",
    )
    op.drop_index(
        op.f("ix_teacher_subscription_transactions_created_at"),
        table_name="teacher_subscription_transactions",
    )
    op.drop_table("teacher_subscription_transactions")

    # 回滾外鍵和約束變更
    op.drop_constraint("unique_classroom_student", "classroom_students", type_="unique")
    op.drop_constraint(
        "unique_student_item_progress", "student_item_progress", type_="unique"
    )
    op.create_unique_constraint(
        "_student_item_progress_uc",
        "student_item_progress",
        ["student_assignment_id", "content_item_id"],
    )

    op.create_index("ix_students_email", "students", ["email"], unique=False)
