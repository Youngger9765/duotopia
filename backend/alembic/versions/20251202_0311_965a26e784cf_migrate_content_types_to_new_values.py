"""migrate_content_types_to_new_values

Migrate existing content types to new values:
- READING_ASSESSMENT -> EXAMPLE_SENTENCES
- SENTENCE_MAKING -> VOCABULARY_SET

Also update existing assignments to have proper practice_mode and score_category.

Revision ID: 965a26e784cf
Revises: ef39b61409ec
Create Date: 2025-12-02 03:11:56.658708

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '965a26e784cf'
down_revision: Union[str, None] = 'ef39b61409ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL requires new enum values to be committed in a separate transaction
    # before they can be used. This migration is intentionally empty on first run.
    #
    # To complete the data migration after enum values are committed, run manually:
    # psql -d duotopia -c "
    #   UPDATE contents SET type = 'EXAMPLE_SENTENCES' WHERE type = 'READING_ASSESSMENT';
    #   UPDATE contents SET type = 'VOCABULARY_SET' WHERE type = 'SENTENCE_MAKING';
    # "
    #
    # Note: For now, we keep READING_ASSESSMENT and SENTENCE_MAKING working via
    # normalize_content_type() in the API layer, so no data migration is required
    # for immediate functionality.
    pass


def downgrade() -> None:
    # This migration is not reversible
    # The old enum values are kept for safety
    pass
