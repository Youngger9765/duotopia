"""add_new_content_types_to_enum

Revision ID: 090076973179
Revises: e01687cd2904
Create Date: 2026-01-15 08:26:28.827411

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '090076973179'
down_revision: Union[str, None] = 'e01687cd2904'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new content types to the contenttype enum
    # Note: PostgreSQL doesn't support removing enum values in downgrade,
    # so we only add them here
    op.execute("ALTER TYPE contenttype ADD VALUE IF NOT EXISTS 'example_sentences'")
    op.execute("ALTER TYPE contenttype ADD VALUE IF NOT EXISTS 'vocabulary_set'")
    op.execute("ALTER TYPE contenttype ADD VALUE IF NOT EXISTS 'single_choice_quiz'")
    op.execute("ALTER TYPE contenttype ADD VALUE IF NOT EXISTS 'scenario_dialogue'")


def downgrade() -> None:
    # PostgreSQL doesn't support dropping enum values
    # The values will remain in the database even after downgrade
    # This is generally safe as they won't be used if the code is rolled back
    pass
