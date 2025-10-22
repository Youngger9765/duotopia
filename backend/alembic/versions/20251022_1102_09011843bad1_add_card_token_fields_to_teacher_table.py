"""Add card token fields to teacher table

Revision ID: 09011843bad1
Revises: 021036b2ccd6
Create Date: 2025-10-22 11:02:37.733764

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "09011843bad1"
down_revision: Union[str, None] = "021036b2ccd6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 新增 TapPay 信用卡 Token 相關欄位
    op.add_column(
        "teachers", sa.Column("card_key", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "teachers", sa.Column("card_token", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "teachers", sa.Column("card_last_four", sa.String(length=4), nullable=True)
    )
    op.add_column(
        "teachers", sa.Column("card_bin_code", sa.String(length=6), nullable=True)
    )
    op.add_column("teachers", sa.Column("card_type", sa.Integer(), nullable=True))
    op.add_column("teachers", sa.Column("card_funding", sa.Integer(), nullable=True))
    op.add_column(
        "teachers", sa.Column("card_issuer", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "teachers", sa.Column("card_country", sa.String(length=2), nullable=True)
    )
    op.add_column(
        "teachers",
        sa.Column("card_saved_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    # 移除 TapPay 信用卡 Token 相關欄位
    op.drop_column("teachers", "card_saved_at")
    op.drop_column("teachers", "card_country")
    op.drop_column("teachers", "card_issuer")
    op.drop_column("teachers", "card_funding")
    op.drop_column("teachers", "card_type")
    op.drop_column("teachers", "card_bin_code")
    op.drop_column("teachers", "card_last_four")
    op.drop_column("teachers", "card_token")
    op.drop_column("teachers", "card_key")
