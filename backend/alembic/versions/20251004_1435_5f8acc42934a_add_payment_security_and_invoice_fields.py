"""add_comprehensive_payment_security_fields

Revision ID: 5f8acc42934a
Revises: 51eb2968653a
Create Date: 2025-10-04 14:35:33.419934

Add security, audit, and tracking fields for payment transactions:
- User identification (teacher_email)
- Idempotency and retry management
- Audit trail (IP, user agent, request ID)
- Payment provider details
- Error handling fields
- Refund tracking
- Webhook status tracking

Note: Invoice data is handled by TapPay e-invoice service, no local storage needed.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5f8acc42934a"
down_revision: Union[str, None] = "51eb2968653a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 用戶識別欄位
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("teacher_email", sa.String(255), nullable=True),
    )

    # 2. 防重複扣款欄位
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("idempotency_key", sa.String(255), nullable=True),
    )
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
    )

    # 3. 稽核追蹤欄位
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("ip_address", sa.String(45), nullable=True),
    )  # 支援 IPv6
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("user_agent", sa.Text(), nullable=True),
    )
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("request_id", sa.String(255), nullable=True),
    )

    # 4. 錯誤處理欄位
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("failure_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("error_code", sa.String(50), nullable=True),
    )
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("gateway_response", sa.JSON(), nullable=True),
    )

    # 5. 支付詳情欄位
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("payment_provider", sa.String(50), nullable=True),
    )
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("payment_method", sa.String(50), nullable=True),
    )
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("external_transaction_id", sa.String(255), nullable=True),
    )

    # 6. 退款相關欄位
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column(
            "refunded_amount", sa.Numeric(10, 2), nullable=True, server_default="0"
        ),
    )
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("refund_status", sa.String(20), nullable=True),
    )
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("original_transaction_id", sa.Integer(), nullable=True),
    )

    # 7. 其他重要欄位
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("webhook_status", sa.String(20), nullable=True),
    )
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 更新現有記錄的 teacher_email（從 teachers 表取得）
    op.execute(
        """
        UPDATE teacher_subscription_transactions tst
        SET teacher_email = t.email
        FROM teachers t
        WHERE tst.teacher_id = t.id AND tst.teacher_email IS NULL
    """
    )

    # 創建索引以提高查詢效能
    op.create_index(
        "idx_tst_teacher_email", "teacher_subscription_transactions", ["teacher_email"]
    )
    op.create_index(
        "idx_tst_idempotency_key",
        "teacher_subscription_transactions",
        ["idempotency_key"],
    )
    op.create_index(
        "idx_tst_external_transaction_id",
        "teacher_subscription_transactions",
        ["external_transaction_id"],
    )
    op.create_index(
        "idx_tst_payment_provider",
        "teacher_subscription_transactions",
        ["payment_provider"],
    )
    op.create_index("idx_tst_status", "teacher_subscription_transactions", ["status"])
    op.create_index(
        "idx_tst_created_at", "teacher_subscription_transactions", ["created_at"]
    )

    # 創建唯一約束防止重複扣款
    op.create_unique_constraint(
        "uq_tst_idempotency_key",
        "teacher_subscription_transactions",
        ["idempotency_key"],
    )

    # 為退款添加外鍵約束
    op.create_foreign_key(
        "fk_tst_original_transaction",
        "teacher_subscription_transactions",
        "teacher_subscription_transactions",
        ["original_transaction_id"],
        ["id"],
    )


def downgrade() -> None:
    # 移除外鍵約束
    op.drop_constraint(
        "fk_tst_original_transaction",
        "teacher_subscription_transactions",
        type_="foreignkey",
    )

    # 移除唯一約束
    op.drop_constraint(
        "uq_tst_idempotency_key", "teacher_subscription_transactions", type_="unique"
    )

    # 移除索引
    op.drop_index("idx_tst_created_at", "teacher_subscription_transactions")
    op.drop_index("idx_tst_status", "teacher_subscription_transactions")
    op.drop_index("idx_tst_payment_provider", "teacher_subscription_transactions")
    op.drop_index(
        "idx_tst_external_transaction_id", "teacher_subscription_transactions"
    )
    op.drop_index("idx_tst_idempotency_key", "teacher_subscription_transactions")
    op.drop_index("idx_tst_teacher_email", "teacher_subscription_transactions")

    # 移除欄位（按相反順序）
    op.drop_column("teacher_subscription_transactions", "expires_at")
    op.drop_column("teacher_subscription_transactions", "processed_at")
    op.drop_column("teacher_subscription_transactions", "webhook_status")
    op.drop_column("teacher_subscription_transactions", "original_transaction_id")
    op.drop_column("teacher_subscription_transactions", "refund_status")
    op.drop_column("teacher_subscription_transactions", "refunded_amount")
    op.drop_column("teacher_subscription_transactions", "external_transaction_id")
    op.drop_column("teacher_subscription_transactions", "payment_method")
    op.drop_column("teacher_subscription_transactions", "payment_provider")
    op.drop_column("teacher_subscription_transactions", "gateway_response")
    op.drop_column("teacher_subscription_transactions", "error_code")
    op.drop_column("teacher_subscription_transactions", "failure_reason")
    op.drop_column("teacher_subscription_transactions", "request_id")
    op.drop_column("teacher_subscription_transactions", "user_agent")
    op.drop_column("teacher_subscription_transactions", "ip_address")
    op.drop_column("teacher_subscription_transactions", "retry_count")
    op.drop_column("teacher_subscription_transactions", "idempotency_key")
    op.drop_column("teacher_subscription_transactions", "teacher_email")
