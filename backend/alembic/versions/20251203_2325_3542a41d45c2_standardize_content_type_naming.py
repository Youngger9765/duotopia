"""standardize_content_type_naming

Revision ID: 3542a41d45c2
Revises: df36fccbe04c
Create Date: 2025-12-03 23:25:43.116532

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3542a41d45c2'
down_revision: Union[str, None] = 'df36fccbe04c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 統一 Content Type 命名
    # READING_ASSESSMENT → EXAMPLE_SENTENCES
    # SENTENCE_MAKING → VOCABULARY_SET

    # 更新 contents 表
    op.execute("""
        UPDATE contents
        SET type = 'EXAMPLE_SENTENCES'
        WHERE type = 'READING_ASSESSMENT'
    """)

    op.execute("""
        UPDATE contents
        SET type = 'VOCABULARY_SET'
        WHERE type = 'SENTENCE_MAKING'
    """)


def downgrade() -> None:
    # 回滾（如果需要）
    op.execute("""
        UPDATE contents
        SET type = 'READING_ASSESSMENT'
        WHERE type = 'EXAMPLE_SENTENCES'
    """)

    op.execute("""
        UPDATE contents
        SET type = 'SENTENCE_MAKING'
        WHERE type = 'VOCABULARY_SET'
    """)
