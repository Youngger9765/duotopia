"""fix_remaining_staging_differences

Revision ID: ce5a518c2519
Revises: 4981d39d8c03
Create Date: 2025-09-22 15:29:58.334379

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ce5a518c2519"
down_revision: Union[str, None] = "4981d39d8c03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """修復剩餘的 staging 差異"""

    # 1. 刪除不需要的索引
    op.drop_index(
        "ix_teacher_subscription_transactions_created_at",
        table_name="teacher_subscription_transactions",
    )
    op.drop_index(
        "ix_teacher_subscription_transactions_status",
        table_name="teacher_subscription_transactions",
    )
    op.drop_index(
        "ix_teacher_subscription_transactions_teacher_id",
        table_name="teacher_subscription_transactions",
    )

    # 2. 創建 Enum type 並修改 transaction_type
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE transactiontype AS ENUM ('TRIAL', 'RECHARGE', 'EXPIRED', 'REFUND');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """
    )

    op.execute(
        """
        ALTER TABLE teacher_subscription_transactions
        ALTER COLUMN transaction_type TYPE transactiontype
        USING transaction_type::transactiontype
    """
    )

    # 3. 修改 nullable 設定
    op.alter_column(
        "teacher_subscription_transactions",
        "months",
        existing_type=sa.Integer(),
        nullable=False,
        existing_nullable=True,
    )

    op.alter_column(
        "teacher_subscription_transactions",
        "new_end_date",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
        existing_nullable=True,
    )


def downgrade() -> None:
    """回滾變更"""

    # 回滾 nullable 設定
    op.alter_column(
        "teacher_subscription_transactions",
        "new_end_date",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
        existing_nullable=False,
    )

    op.alter_column(
        "teacher_subscription_transactions",
        "months",
        existing_type=sa.Integer(),
        nullable=True,
        existing_nullable=False,
    )

    # 回滾 enum 到 varchar
    op.execute(
        """
        ALTER TABLE teacher_subscription_transactions
        ALTER COLUMN transaction_type TYPE VARCHAR
        USING transaction_type::text
    """
    )

    # 重新創建索引
    op.create_index(
        "ix_teacher_subscription_transactions_teacher_id",
        "teacher_subscription_transactions",
        ["teacher_id"],
    )
    op.create_index(
        "ix_teacher_subscription_transactions_status",
        "teacher_subscription_transactions",
        ["status"],
    )
    op.create_index(
        "ix_teacher_subscription_transactions_created_at",
        "teacher_subscription_transactions",
        ["created_at"],
    )
