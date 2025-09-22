"""Add additional fields to teacher subscription transaction model

Revision ID: a3cf45fb8eea
Revises: 75d0959d6f50
Create Date: 2025-09-21 23:45:55.171885

這個 migration 新增額外的欄位到已存在的 teacher_subscription_transactions 表
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a3cf45fb8eea"
down_revision: Union[str, None] = "75d0959d6f50"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """新增額外欄位到 teacher_subscription_transactions 表"""

    # 1. 建立 Enum type for transaction_type (如果不存在)
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE transactiontype AS ENUM ('TRIAL', 'RECHARGE', 'EXPIRED', 'REFUND');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """
    )

    # 2. 新增額外的欄位到現有表格
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("months", sa.Integer(), nullable=True),
    )
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("previous_end_date", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("new_end_date", sa.DateTime(timezone=True), nullable=True),
    )

    # 3. 修改 transaction_type 欄位使用 Enum (如果需要)
    # 注意：這裡先保持原本的 String 類型，避免破壞現有資料
    # 未來可以在另一個 migration 中轉換為 Enum

    # 4. 建立索引 (只建立 id 索引，teacher_id 索引已在 75d0959d6f50 創建)
    op.create_index(
        op.f("ix_teacher_subscription_transactions_id"),
        "teacher_subscription_transactions",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    """移除新增的欄位"""
    op.drop_index(
        op.f("ix_teacher_subscription_transactions_id"),
        table_name="teacher_subscription_transactions",
    )
    op.drop_column("teacher_subscription_transactions", "new_end_date")
    op.drop_column("teacher_subscription_transactions", "previous_end_date")
    op.drop_column("teacher_subscription_transactions", "months")

    # 移除 Enum type (如果沒有其他表在使用)
    op.execute("DROP TYPE IF EXISTS transactiontype")
