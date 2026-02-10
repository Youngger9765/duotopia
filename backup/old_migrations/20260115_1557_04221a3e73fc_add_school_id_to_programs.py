"""add_school_id_to_programs

Revision ID: 04221a3e73fc
Revises: 090076973179
Create Date: 2026-01-15 15:57:11.722095

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '04221a3e73fc'
down_revision: Union[str, None] = '090076973179'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add school_id column to programs table
    op.add_column(
        'programs',
        sa.Column('school_id', sa.UUID(), nullable=True)
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_programs_school_id',
        'programs',
        'schools',
        ['school_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Add index for performance
    op.create_index(
        'ix_programs_school_id',
        'programs',
        ['school_id']
    )


def downgrade() -> None:
    op.drop_index('ix_programs_school_id', table_name='programs')
    op.drop_constraint('fk_programs_school_id', 'programs', type_='foreignkey')
    op.drop_column('programs', 'school_id')
