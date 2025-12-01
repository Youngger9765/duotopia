"""add_assignment_copy_fields_and_performance_indexes

合併 migration：
1. 新增作業副本機制欄位（is_assignment_copy, source_content_id）
2. 添加性能索引（AssignmentContent, StudentContentProgress, StudentItemProgress）

Revision ID: cd6eab4e2001
Revises: 289edf7e0aa8
Create Date: 2025-12-01 23:36:35.016764

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd6eab4e2001'
down_revision: Union[str, None] = '289edf7e0aa8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============ 新增作業副本機制欄位 ============
    op.add_column(
        "contents",
        sa.Column("is_assignment_copy", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "contents",
        sa.Column("source_content_id", sa.Integer(), nullable=True),
    )
    
    # 建立索引以提升查詢效率
    op.create_index(
        "ix_contents_is_assignment_copy",
        "contents",
        ["is_assignment_copy"],
        unique=False,
    )
    
    # 建立外鍵約束
    op.create_foreign_key(
        "fk_contents_source_content_id",
        "contents",
        "contents",
        ["source_content_id"],
        ["id"],
    )

    # 建立 source_content_id 索引（優化查找所有副本的查詢）
    op.create_index(
        "ix_contents_source_content_id",
        "contents",
        ["source_content_id"],
        unique=False,
    )

    # ============ 添加性能索引 ============
    # 添加 AssignmentContent 複合索引（優化查詢排序）
    op.create_index(
        "ix_assignment_content_assignment_order",
        "assignment_contents",
        ["assignment_id", "order_index"],
        unique=False,
    )
    
    # 添加 StudentContentProgress 複合索引（優化查詢排序）
    op.create_index(
        "ix_student_content_progress_assignment_order",
        "student_content_progress",
        ["student_assignment_id", "order_index"],
        unique=False,
    )
    
    # 添加 StudentItemProgress 索引（優化查詢）
    op.create_index(
        "ix_student_item_progress_assignment",
        "student_item_progress",
        ["student_assignment_id"],
        unique=False,
    )


def downgrade() -> None:
    # ============ 移除性能索引 ============
    op.drop_index("ix_student_item_progress_assignment", table_name="student_item_progress")
    op.drop_index("ix_student_content_progress_assignment_order", table_name="student_content_progress")
    op.drop_index("ix_assignment_content_assignment_order", table_name="assignment_contents")
    
    # ============ 移除作業副本機制欄位 ============
    # 移除外鍵約束
    op.drop_constraint("fk_contents_source_content_id", "contents", type_="foreignkey")

    # 移除索引
    op.drop_index("ix_contents_source_content_id", table_name="contents")
    op.drop_index("ix_contents_is_assignment_copy", table_name="contents")
    
    # 移除欄位
    op.drop_column("contents", "source_content_id")
    op.drop_column("contents", "is_assignment_copy")
