"""add_role_to_teacher

Revision ID: bd819e7faa26
Revises: b6fb1f60db50
Create Date: 2025-10-27 06:38:53.540922

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd819e7faa26'
down_revision: Union[str, None] = 'b6fb1f60db50'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加 role 欄位，預設值為 'teacher'
    op.add_column('teachers', sa.Column('role', sa.String(length=20), nullable=False, server_default='teacher'))

    # 移除 server_default（只在創建時需要，之後由 model 的 default 處理）
    op.alter_column('teachers', 'role', server_default=None)


def downgrade() -> None:
    # 移除 role 欄位
    op.drop_column('teachers', 'role')
