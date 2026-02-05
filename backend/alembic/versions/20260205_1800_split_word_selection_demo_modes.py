"""Split demo_word_selection_assignment_id into listening and writing modes

Revision ID: 20260205_1800
Revises: 20260203_1600
Create Date: 2026-02-05 18:00:00.000000

This migration adds two new demo config keys:
- demo_word_selection_listening_assignment_id: 單字聽力選擇 Demo 作業 ID
- demo_word_selection_writing_assignment_id: 單字選擇 Demo 作業 ID

The old demo_word_selection_assignment_id is preserved for backward compatibility.
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260205_1800"
down_revision = "20260203_1600"
depends_on = None


def upgrade():
    """Add two new demo config keys for word selection modes (idempotent)"""
    # Insert new keys with ON CONFLICT DO NOTHING for idempotency
    op.execute(
        """
        INSERT INTO demo_config (key, value, description) VALUES
            ('demo_word_selection_listening_assignment_id', NULL, '單字聽力選擇 Demo 作業 ID'),
            ('demo_word_selection_writing_assignment_id', NULL, '單字選擇 Demo 作業 ID')
        ON CONFLICT (key) DO NOTHING;
    """
    )


def downgrade():
    """Remove the new keys (not dropping old key for safety)"""
    op.execute(
        """
        DELETE FROM demo_config
        WHERE key IN (
            'demo_word_selection_listening_assignment_id',
            'demo_word_selection_writing_assignment_id'
        );
    """
    )
