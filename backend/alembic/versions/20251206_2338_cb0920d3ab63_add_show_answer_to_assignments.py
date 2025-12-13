"""add_show_answer_to_assignments

Revision ID: cb0920d3ab63
Revises: 9ecbb63fa545
Create Date: 2025-12-06 23:38:51.205871

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "cb0920d3ab63"
down_revision: Union[str, None] = "9ecbb63fa545"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 新增 show_answer 欄位（答題結束後是否顯示正確答案）
    # 使用 IF NOT EXISTS 確保在共用資料庫環境中不會重複新增
    op.execute(
        """
        ALTER TABLE assignments
        ADD COLUMN IF NOT EXISTS show_answer BOOLEAN DEFAULT FALSE
    """
    )


def downgrade() -> None:
    # 注意：downgrade 不使用，因為我們遵循 additive-only migration 原則
    pass
