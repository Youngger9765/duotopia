"""add_organization_id_to_programs

Revision ID: e01687cd2904
Revises: b2c3d4e5f6a7
Create Date: 2026-01-14 15:27:19.290271

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e01687cd2904'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add organization_id column to programs table
    # This column identifies organization-owned materials (NOT classroom copies)
    # Nullable=True because existing programs may not have this set
    op.add_column(
        'programs',
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_programs_organization_id',
        'programs',
        'organizations',
        ['organization_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Add index for performance (organization materials queries will filter by this)
    op.create_index(
        'ix_programs_organization_id',
        'programs',
        ['organization_id']
    )

    # Migrate existing data: Extract organization_id from source_metadata JSON
    # Only for template programs where source_metadata.organization_id exists
    # Note: Using JSONB cast to support the ? operator
    op.execute("""
        UPDATE programs
        SET organization_id = CAST(source_metadata->>'organization_id' AS UUID)
        WHERE is_template = true
          AND source_metadata IS NOT NULL
          AND CAST(source_metadata AS JSONB) ? 'organization_id'
          AND source_metadata->>'organization_id' IS NOT NULL
          AND source_metadata->>'organization_id' ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    """)


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_programs_organization_id', table_name='programs')

    # Drop foreign key constraint
    op.drop_constraint('fk_programs_organization_id', 'programs', type_='foreignkey')

    # Drop column
    op.drop_column('programs', 'organization_id')
