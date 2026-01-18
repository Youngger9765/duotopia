"""merge_develop_vocabulary_and_staging

Revision ID: 808d3ca352c0
Revises: d21f6f58c952, f8c2d3e4a5b6
Create Date: 2026-01-18 18:19:39.836920

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "808d3ca352c0"
down_revision: Union[str, None] = ("d21f6f58c952", "f8c2d3e4a5b6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
