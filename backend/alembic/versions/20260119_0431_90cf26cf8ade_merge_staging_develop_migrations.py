"""merge_staging_develop_migrations

Revision ID: 90cf26cf8ade
Revises: d21f6f58c952, f8c2d3e4a5b6
Create Date: 2026-01-19 04:31:38.449825

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "90cf26cf8ade"
down_revision: Union[str, None] = ("d21f6f58c952", "f8c2d3e4a5b6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
