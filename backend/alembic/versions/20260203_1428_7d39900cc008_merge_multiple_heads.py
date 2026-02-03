"""merge_multiple_heads

Revision ID: 7d39900cc008
Revises: g2b3c4d5e6f7, 20260203_0143
Create Date: 2026-02-03 14:28:05.098933

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d39900cc008'
down_revision: Union[str, None] = ('g2b3c4d5e6f7', '20260203_0143')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
