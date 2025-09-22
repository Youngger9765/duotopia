"""recreate_students_email_index

Revision ID: 4981d39d8c03
Revises: 12578a583628
Create Date: 2025-09-22 14:51:45.515991

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "4981d39d8c03"
down_revision: Union[str, None] = "12578a583628"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """重新創建被 75d0959d6f50 錯誤刪除的 students.email 索引"""
    # Student model 有 index=True，所以需要這個索引
    op.create_index("ix_students_email", "students", ["email"])


def downgrade() -> None:
    """移除索引"""
    op.drop_index("ix_students_email", table_name="students")
