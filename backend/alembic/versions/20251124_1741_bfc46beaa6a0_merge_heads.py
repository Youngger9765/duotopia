"""merge heads

Revision ID: bfc46beaa6a0
Revises: 666c291b851d, 30e72978e174
Create Date: 2025-11-24 17:41:38.201398

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bfc46beaa6a0"
down_revision: Union[str, None] = ("666c291b851d", "30e72978e174")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
