"""add performance indexes

Revision ID: 20251105_0620
Revises: f42b27a78bec
Create Date: 2025-11-05 06:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251105_0620"
down_revision = "f42b27a78bec"
branch_labels = None
depends_on = None


def upgrade():
    # 1. subscription_periods - 最常查詢的條件
    # 查詢 current_period 時用 (teacher_id, status)
    op.create_index(
        "ix_subscription_periods_teacher_status",
        "subscription_periods",
        ["teacher_id", "status"],
        unique=False,
    )

    # 查詢時間範圍（查詢過期訂閱）
    op.create_index(
        "ix_subscription_periods_end_date",
        "subscription_periods",
        ["end_date"],
        unique=False,
    )

    # 2. point_usage_logs - 查詢使用記錄
    # 按 teacher 查詢使用記錄
    op.create_index(
        "ix_point_usage_logs_teacher_id",
        "point_usage_logs",
        ["teacher_id"],
        unique=False,
    )

    # 按 subscription_period 查詢使用記錄
    op.create_index(
        "ix_point_usage_logs_period_id",
        "point_usage_logs",
        ["subscription_period_id"],
        unique=False,
    )

    # 按時間查詢（統計分析用）
    op.create_index(
        "ix_point_usage_logs_created_at",
        "point_usage_logs",
        ["created_at"],
        unique=False,
    )

    # 按 feature_type 查詢（功能使用統計）
    op.create_index(
        "ix_point_usage_logs_feature_type",
        "point_usage_logs",
        ["feature_type"],
        unique=False,
    )

    # 複合索引：teacher + created_at（常用於統計分析）
    op.create_index(
        "ix_point_usage_logs_teacher_created",
        "point_usage_logs",
        ["teacher_id", "created_at"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_point_usage_logs_teacher_created", table_name="point_usage_logs")
    op.drop_index("ix_point_usage_logs_feature_type", table_name="point_usage_logs")
    op.drop_index("ix_point_usage_logs_created_at", table_name="point_usage_logs")
    op.drop_index("ix_point_usage_logs_period_id", table_name="point_usage_logs")
    op.drop_index("ix_point_usage_logs_teacher_id", table_name="point_usage_logs")
    op.drop_index("ix_subscription_periods_end_date", table_name="subscription_periods")
    op.drop_index(
        "ix_subscription_periods_teacher_status", table_name="subscription_periods"
    )
