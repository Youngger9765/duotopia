"""fix_max_errors_calculation

Revision ID: df36fccbe04c
Revises: 965a26e784cf
Create Date: 2025-12-03 23:10:28.669481

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'df36fccbe04c'
down_revision: Union[str, None] = '965a26e784cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 更新所有 ContentItem 的 word_count 和 max_errors
    # 規則：2-10 字 → 3 次允許錯誤，11-25 字 → 5 次允許錯誤

    # 先更新 word_count（根據 text 欄位計算字數）
    op.execute("""
        UPDATE content_items
        SET word_count = array_length(regexp_split_to_array(trim(text), '\s+'), 1)
        WHERE text IS NOT NULL AND trim(text) != ''
    """)

    # 再更新 max_errors（根據 word_count 計算）
    op.execute("""
        UPDATE content_items
        SET max_errors = CASE
            WHEN word_count IS NULL OR word_count <= 10 THEN 3
            ELSE 5
        END
        WHERE text IS NOT NULL AND trim(text) != ''
    """)


def downgrade() -> None:
    pass
