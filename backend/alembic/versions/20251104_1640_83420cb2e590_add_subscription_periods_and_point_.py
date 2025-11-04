"""add_subscription_periods_and_point_usage_logs

Revision ID: 83420cb2e590
Revises: b6fb1f60db50
Create Date: 2025-11-04 16:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "83420cb2e590"
down_revision: Union[str, None] = "b6fb1f60db50"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========== 1. 創建 subscription_periods 表 ==========
    op.create_table(
        "subscription_periods",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        # 訂閱資訊
        sa.Column("plan_name", sa.String(), nullable=False),
        sa.Column("amount_paid", sa.Integer(), nullable=False),
        sa.Column("quota_total", sa.Integer(), nullable=False),
        sa.Column("quota_used", sa.Integer(), nullable=False, server_default="0"),
        # 時間範圍
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        # 付款資訊
        sa.Column("payment_method", sa.String(), nullable=False),
        sa.Column("payment_id", sa.String(), nullable=True),
        sa.Column("payment_status", sa.String(), nullable=False, server_default="paid"),
        # 狀態
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_reason", sa.String(), nullable=True),
        # 時間戳
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True
        ),
        # 主鍵與外鍵
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="CASCADE"),
    )

    # 創建索引
    op.create_index(
        "ix_subscription_periods_teacher_id", "subscription_periods", ["teacher_id"]
    )
    op.create_index("ix_subscription_periods_status", "subscription_periods", ["status"])
    op.create_index(
        "ix_subscription_periods_dates",
        "subscription_periods",
        ["start_date", "end_date"],
    )

    # ========== 2. 創建 point_usage_logs 表 ==========
    op.create_table(
        "point_usage_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        # 關聯
        sa.Column("subscription_period_id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=True),
        sa.Column("assignment_id", sa.Integer(), nullable=True),
        # 功能資訊
        sa.Column("feature_type", sa.String(), nullable=False),
        sa.Column("feature_detail", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        # 點數消耗
        sa.Column("points_used", sa.Integer(), nullable=False),
        sa.Column("quota_before", sa.Integer(), nullable=True),
        sa.Column("quota_after", sa.Integer(), nullable=True),
        # 單位資訊
        sa.Column("unit_count", sa.Float(), nullable=True),
        sa.Column("unit_type", sa.String(), nullable=True),
        # 時間
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        # 主鍵與外鍵
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["subscription_period_id"],
            ["subscription_periods.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="SET NULL"),
    )

    # 創建索引
    op.create_index("ix_point_usage_logs_teacher_id", "point_usage_logs", ["teacher_id"])
    op.create_index("ix_point_usage_logs_student_id", "point_usage_logs", ["student_id"])
    op.create_index(
        "ix_point_usage_logs_subscription_period_id",
        "point_usage_logs",
        ["subscription_period_id"],
    )
    op.create_index(
        "ix_point_usage_logs_created_at", "point_usage_logs", ["created_at"]
    )

    # ========== 3. 遷移現有資料 ==========
    op.execute(
        """
        INSERT INTO subscription_periods (
            teacher_id,
            plan_name,
            amount_paid,
            quota_total,
            quota_used,
            start_date,
            end_date,
            payment_method,
            payment_id,
            payment_status,
            status,
            created_at
        )
        SELECT
            id as teacher_id,
            COALESCE(subscription_type, 'Tutor Teachers') as plan_name,
            CASE
                WHEN COALESCE(subscription_type, 'Tutor Teachers') = 'School Teachers' THEN 660
                ELSE 330
            END as amount_paid,
            CASE
                WHEN COALESCE(subscription_type, 'Tutor Teachers') = 'School Teachers' THEN 4000
                ELSE 1800
            END as quota_total,
            0 as quota_used,
            COALESCE(subscription_renewed_at, created_at) as start_date,
            subscription_end_date as end_date,
            CASE
                WHEN subscription_auto_renew = true THEN 'auto_renew'
                ELSE 'manual'
            END as payment_method,
            NULL as payment_id,
            'paid' as payment_status,
            CASE
                WHEN subscription_end_date > NOW() THEN 'active'
                ELSE 'expired'
            END as status,
            COALESCE(subscription_renewed_at, created_at) as created_at
        FROM teachers
        WHERE subscription_end_date IS NOT NULL
    """
    )


def downgrade() -> None:
    # 刪除 point_usage_logs 表
    op.drop_index("ix_point_usage_logs_created_at", table_name="point_usage_logs")
    op.drop_index(
        "ix_point_usage_logs_subscription_period_id", table_name="point_usage_logs"
    )
    op.drop_index("ix_point_usage_logs_student_id", table_name="point_usage_logs")
    op.drop_index("ix_point_usage_logs_teacher_id", table_name="point_usage_logs")
    op.drop_table("point_usage_logs")

    # 刪除 subscription_periods 表
    op.drop_index("ix_subscription_periods_dates", table_name="subscription_periods")
    op.drop_index("ix_subscription_periods_status", table_name="subscription_periods")
    op.drop_index("ix_subscription_periods_teacher_id", table_name="subscription_periods")
    op.drop_table("subscription_periods")
