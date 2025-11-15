"""add_is_admin_to_teachers

Revision ID: da1cbac127b2
Revises: 5cff70f7dc07
Create Date: 2025-11-15 11:27:48.014416

新增 Admin 權限管理：
- 在 teachers 表新增 is_admin 欄位
- 預設值為 False（一般教師）
- 設定初始 admin 帳號
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "da1cbac127b2"
down_revision: Union[str, None] = "5cff70f7dc07"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 新增 is_admin 欄位
    op.add_column(
        "teachers",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
    )

    # 設定初始 admin 帳號
    op.execute(
        """
        UPDATE teachers
        SET is_admin = TRUE
        WHERE email IN (
            'kaddyeunice@apps.ntpc.edu.tw',
            'ceeks.edu@gmail.com',
            'purpleice9765@msn.com'
        )
    """
    )


def downgrade() -> None:
    # 移除 is_admin 欄位
    op.drop_column("teachers", "is_admin")
