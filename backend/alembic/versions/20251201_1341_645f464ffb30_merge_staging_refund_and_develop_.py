"""merge staging refund and develop sentence_making

Revision ID: 645f464ffb30
Revises: 289edf7e0aa8, 0a267f39cda8
Create Date: 2025-12-01 13:41:55.975165

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '645f464ffb30'
down_revision: Union[str, None] = ('289edf7e0aa8', '0a267f39cda8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
