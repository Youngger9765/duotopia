"""merge staging and develop migrations

Revision ID: 9ecbb63fa545
Revises: 288ad5a75206, 3542a41d45c2
Create Date: 2025-12-04 16:10:29.287746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ecbb63fa545'
down_revision: Union[str, None] = ('288ad5a75206', '3542a41d45c2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
