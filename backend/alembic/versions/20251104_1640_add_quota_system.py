"""add quota system (subscription_periods and point_usage_logs)

Revision ID: 20251104_1640
Revises: b6fb1f60db50
Create Date: 2025-11-04 16:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20251104_1640"
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
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            onupdate=sa.func.now(),
            nullable=True,
        ),
        # 主鍵與外鍵
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="CASCADE"),
    )

    # 創建 subscription_periods 索引（優化版）
    op.create_index(
        op.f("ix_subscription_periods_id"), "subscription_periods", ["id"], unique=False
    )
    op.create_index(
        "ix_subscription_periods_teacher_status",
        "subscription_periods",
        ["teacher_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_subscription_periods_end_date",
        "subscription_periods",
        ["end_date"],
        unique=False,
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
        sa.Column(
            "feature_detail", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
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
            nullable=True,
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

    # 創建 point_usage_logs 索引（優化版）
    op.create_index(
        op.f("ix_point_usage_logs_id"), "point_usage_logs", ["id"], unique=False
    )
    op.create_index(
        "ix_point_usage_logs_teacher_id",
        "point_usage_logs",
        ["teacher_id"],
        unique=False,
    )
    op.create_index(
        "ix_point_usage_logs_period_id",
        "point_usage_logs",
        ["subscription_period_id"],
        unique=False,
    )
    op.create_index(
        "ix_point_usage_logs_created_at",
        "point_usage_logs",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_point_usage_logs_feature_type",
        "point_usage_logs",
        ["feature_type"],
        unique=False,
    )
    op.create_index(
        "ix_point_usage_logs_teacher_created",
        "point_usage_logs",
        ["teacher_id", "created_at"],
        unique=False,
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
                WHEN COALESCE(subscription_type, 'Tutor Teachers') = 'School Teachers' THEN 25000
                ELSE 10000
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

    # ========== 4. 啟用 RLS ==========
    op.execute("ALTER TABLE subscription_periods ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE point_usage_logs ENABLE ROW LEVEL SECURITY")

    # 創建 RLS Policies
    # subscription_periods: 老師只能看到自己的訂閱期間
    op.execute(
        """
        CREATE POLICY subscription_periods_teacher_policy ON subscription_periods
        FOR ALL
        TO authenticated
        USING (teacher_id = current_setting('app.current_teacher_id', TRUE)::integer)
    """
    )

    # point_usage_logs: 老師只能看到自己的使用記錄
    op.execute(
        """
        CREATE POLICY point_usage_logs_teacher_policy ON point_usage_logs
        FOR ALL
        TO authenticated
        USING (teacher_id = current_setting('app.current_teacher_id', TRUE)::integer)
    """
    )


def downgrade() -> None:
    # 移除 RLS policies
    op.execute(
        "DROP POLICY IF EXISTS point_usage_logs_teacher_policy ON point_usage_logs"
    )
    op.execute(
        "DROP POLICY IF EXISTS subscription_periods_teacher_policy ON subscription_periods"
    )

    # 刪除 point_usage_logs 表及索引
    op.drop_index("ix_point_usage_logs_teacher_created", table_name="point_usage_logs")
    op.drop_index("ix_point_usage_logs_feature_type", table_name="point_usage_logs")
    op.drop_index("ix_point_usage_logs_created_at", table_name="point_usage_logs")
    op.drop_index("ix_point_usage_logs_period_id", table_name="point_usage_logs")
    op.drop_index("ix_point_usage_logs_teacher_id", table_name="point_usage_logs")
    op.drop_index(op.f("ix_point_usage_logs_id"), table_name="point_usage_logs")
    op.drop_table("point_usage_logs")

    # 刪除 subscription_periods 表及索引
    op.drop_index("ix_subscription_periods_end_date", table_name="subscription_periods")
    op.drop_index(
        "ix_subscription_periods_teacher_status", table_name="subscription_periods"
    )
    op.drop_index(op.f("ix_subscription_periods_id"), table_name="subscription_periods")
    op.drop_table("subscription_periods")
