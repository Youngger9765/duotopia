"""merge_multiple_heads

Revision ID: d21f6f58c952
Revises: 4566cb74e6f7, cb0920d3ab63, f8a7c3d2e1b0
Create Date: 2026-01-11 12:17:22.248174

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d21f6f58c952"
down_revision: Union[str, None] = ("4566cb74e6f7", "cb0920d3ab63", "f8a7c3d2e1b0")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
