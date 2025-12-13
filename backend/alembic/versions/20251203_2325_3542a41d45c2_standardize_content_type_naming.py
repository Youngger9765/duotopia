"""standardize_content_type_naming

Revision ID: 3542a41d45c2
Revises: df36fccbe04c
Create Date: 2025-12-03 23:25:43.116532

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = "3542a41d45c2"
down_revision: Union[str, None] = "df36fccbe04c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 統一 Content Type 命名
    # READING_ASSESSMENT → EXAMPLE_SENTENCES
    # SENTENCE_MAKING → VOCABULARY_SET
    #
    # 注意：PostgreSQL 要求新的 enum 值必須先 COMMIT 才能使用
    # 所以這裡使用 AUTOCOMMIT 模式執行 UPDATE

    # 獲取連接並設置 autocommit 模式
    connection = op.get_bind()

    # 先提交之前的事務（確保 enum 值已經被添加）
    connection.execute(text("COMMIT"))

    # 使用 autocommit 執行 UPDATE
    connection.execute(
        text(
            """
        UPDATE contents
        SET type = 'EXAMPLE_SENTENCES'
        WHERE type = 'READING_ASSESSMENT'
    """
        )
    )

    connection.execute(
        text(
            """
        UPDATE contents
        SET type = 'VOCABULARY_SET'
        WHERE type = 'SENTENCE_MAKING'
    """
        )
    )

    # 開始新的事務（讓後續的 migration 正常運行）
    connection.execute(text("BEGIN"))


def downgrade() -> None:
    connection = op.get_bind()

    connection.execute(text("COMMIT"))

    connection.execute(
        text(
            """
        UPDATE contents
        SET type = 'READING_ASSESSMENT'
        WHERE type = 'EXAMPLE_SENTENCES'
    """
        )
    )

    connection.execute(
        text(
            """
        UPDATE contents
        SET type = 'SENTENCE_MAKING'
        WHERE type = 'VOCABULARY_SET'
    """
        )
    )

    connection.execute(text("BEGIN"))
