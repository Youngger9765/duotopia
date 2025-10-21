"""add_tappay_einvoice_fields

Revision ID: 021036b2ccd6
Revises: d12004490bb1
Create Date: 2025-10-21 17:39:48.019323

新增 TapPay 電子發票相關欄位與狀態歷史表
- 在 teacher_subscription_transactions 新增發票相關欄位
- 新增 invoice_status_history 表格追蹤發票狀態變更歷史
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "021036b2ccd6"
down_revision: Union[str, None] = "d12004490bb1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 在 teacher_subscription_transactions 新增發票基本欄位
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("rec_invoice_id", sa.String(30), nullable=True),
    )
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("invoice_number", sa.String(10), nullable=True),
    )
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column(
            "invoice_status", sa.String(20), nullable=True, server_default="PENDING"
        ),
    )
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("invoice_issued_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 2. 買受人資訊
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("buyer_tax_id", sa.String(8), nullable=True),
    )
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("buyer_name", sa.String(100), nullable=True),
    )
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("buyer_email", sa.String(255), nullable=True),
    )

    # 3. 載具資訊
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("carrier_type", sa.String(10), nullable=True),
    )
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column("carrier_id", sa.String(64), nullable=True),
    )

    # 4. 發票回應資料
    op.add_column(
        "teacher_subscription_transactions",
        sa.Column(
            "invoice_response", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )

    # 5. 新增索引
    op.create_index(
        "idx_tst_rec_invoice_id",
        "teacher_subscription_transactions",
        ["rec_invoice_id"],
    )
    op.create_index(
        "idx_tst_invoice_number",
        "teacher_subscription_transactions",
        ["invoice_number"],
    )
    op.create_index(
        "idx_tst_invoice_status",
        "teacher_subscription_transactions",
        ["invoice_status"],
    )

    # 6. 新增發票狀態歷史表
    op.create_table(
        "invoice_status_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "transaction_id",
            sa.Integer(),
            sa.ForeignKey("teacher_subscription_transactions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_status", sa.String(20), nullable=True),
        sa.Column("to_status", sa.String(20), nullable=False),
        sa.Column(
            "action_type", sa.String(20), nullable=False
        ),  # ISSUE/VOID/ALLOWANCE/REISSUE/NOTIFY
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("is_notify", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notify_error_code", sa.String(20), nullable=True),
        sa.Column("notify_error_msg", sa.Text(), nullable=True),
        sa.Column(
            "request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # 7. 發票歷史表索引
    op.create_index(
        "idx_invoice_history_transaction_id",
        "invoice_status_history",
        ["transaction_id"],
    )
    op.create_index(
        "idx_invoice_history_created_at",
        "invoice_status_history",
        ["created_at"],
        postgresql_ops={"created_at": "DESC"},
    )


def downgrade() -> None:
    # 移除索引
    op.drop_index("idx_invoice_history_created_at", "invoice_status_history")
    op.drop_index("idx_invoice_history_transaction_id", "invoice_status_history")

    # 移除發票歷史表
    op.drop_table("invoice_status_history")

    # 移除主表索引
    op.drop_index("idx_tst_invoice_status", "teacher_subscription_transactions")
    op.drop_index("idx_tst_invoice_number", "teacher_subscription_transactions")
    op.drop_index("idx_tst_rec_invoice_id", "teacher_subscription_transactions")

    # 移除欄位
    op.drop_column("teacher_subscription_transactions", "invoice_response")
    op.drop_column("teacher_subscription_transactions", "carrier_id")
    op.drop_column("teacher_subscription_transactions", "carrier_type")
    op.drop_column("teacher_subscription_transactions", "buyer_email")
    op.drop_column("teacher_subscription_transactions", "buyer_name")
    op.drop_column("teacher_subscription_transactions", "buyer_tax_id")
    op.drop_column("teacher_subscription_transactions", "invoice_issued_at")
    op.drop_column("teacher_subscription_transactions", "invoice_status")
    op.drop_column("teacher_subscription_transactions", "invoice_number")
    op.drop_column("teacher_subscription_transactions", "rec_invoice_id")
