"""add example sentence fields to content_items

Revision ID: 85160fa3d3cc
Revises: 59686379aa20
Create Date: 2025-11-10 10:33:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "85160fa3d3cc"
down_revision: Union[str, None] = "59686379aa20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add example sentence fields to content_items table
    op.add_column(
        "content_items",
        sa.Column("example_sentence", sa.Text(), nullable=True),
    )
    op.add_column(
        "content_items",
        sa.Column("example_sentence_translation", sa.Text(), nullable=True),
    )
    op.add_column(
        "content_items",
        sa.Column("example_sentence_definition", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    # Remove example sentence fields from content_items table
    op.drop_column("content_items", "example_sentence_definition")
    op.drop_column("content_items", "example_sentence_translation")
    op.drop_column("content_items", "example_sentence")
