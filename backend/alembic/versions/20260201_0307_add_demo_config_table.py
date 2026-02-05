"""Add demo_config table for configurable demo assignment IDs

Revision ID: 20260201_0307
Revises: 20260201_0306
Create Date: 2026-02-01 03:07:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260201_0307"
down_revision = "20260201_0306"
depends_on = None


def upgrade():
    """Create demo_config table if not exists (idempotent)"""
    # Create table with IF NOT EXISTS for idempotency
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS demo_config (
            key VARCHAR(100) PRIMARY KEY,
            value VARCHAR(500),
            description VARCHAR(500),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """
    )

    # Insert default keys with ON CONFLICT DO NOTHING for idempotency
    # Values are NULL by default - will be set via database after creating demo assignments
    op.execute(
        """
        INSERT INTO demo_config (key, value, description) VALUES
            ('demo_reading_assignment_id', NULL, '例句朗讀 Demo 作業 ID'),
            ('demo_rearrangement_assignment_id', NULL, '例句重組 Demo 作業 ID'),
            ('demo_vocabulary_assignment_id', NULL, '單字朗讀 Demo 作業 ID'),
            ('demo_word_selection_assignment_id', NULL, '單字選擇 Demo 作業 ID')
        ON CONFLICT (key) DO NOTHING;
    """
    )


def downgrade():
    """Drop demo_config table"""
    op.execute("DROP TABLE IF EXISTS demo_config;")
