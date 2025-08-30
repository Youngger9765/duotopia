"""properly add level and tags to contents

Revision ID: b5cb932916d7
Revises: b5cb932916d6
Create Date: 2025-08-31 00:21:26.007148

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5cb932916d7'
down_revision: Union[str, None] = 'd6854a5f6c92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add level and tags columns to contents table
    op.add_column('contents', sa.Column('level', sa.String(length=10), nullable=True, server_default='A1'))
    op.add_column('contents', sa.Column('tags', sa.JSON(), nullable=True, server_default='[]'))


def downgrade() -> None:
    # Remove level and tags columns from contents table
    op.drop_column('contents', 'tags')
    op.drop_column('contents', 'level')
