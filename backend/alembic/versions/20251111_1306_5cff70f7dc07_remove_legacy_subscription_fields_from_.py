"""remove legacy subscription fields from teachers table

Revision ID: 5cff70f7dc07
Revises: 20251104_1640
Create Date: 2025-11-11 13:06:03.767021

移除 Teacher 表中已遷移到 subscription_periods 的舊欄位：
- subscription_type
- subscription_status
- subscription_start_date
- subscription_end_date
- subscription_renewed_at
- monthly_message_limit
- messages_used_this_month

這些欄位已全部遷移到 subscription_periods 表，
並通過 @property 方法向後兼容。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '5cff70f7dc07'
down_revision: Union[str, None] = '20251104_1640'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """移除舊的訂閱欄位"""
    # 刪除 7 個舊欄位
    with op.batch_alter_table("teachers", schema=None) as batch_op:
        batch_op.drop_column("subscription_type")
        batch_op.drop_column("subscription_status")
        batch_op.drop_column("subscription_start_date")
        batch_op.drop_column("subscription_end_date")
        batch_op.drop_column("subscription_renewed_at")
        batch_op.drop_column("monthly_message_limit")
        batch_op.drop_column("messages_used_this_month")


def downgrade() -> None:
    """恢復舊欄位（用於回滾）"""
    with op.batch_alter_table("teachers", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("subscription_type", sa.String(length=50), nullable=True)
        )
        batch_op.add_column(
            sa.Column("subscription_status", sa.String(length=50), nullable=True)
        )
        batch_op.add_column(
            sa.Column("subscription_start_date", postgresql.TIMESTAMP(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("subscription_end_date", postgresql.TIMESTAMP(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("subscription_renewed_at", postgresql.TIMESTAMP(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("monthly_message_limit", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("messages_used_this_month", sa.Integer(), nullable=True)
        )
