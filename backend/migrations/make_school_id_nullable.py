"""Make school_id nullable for individual teacher support

This migration allows classrooms to exist without a school_id,
supporting individual teachers who don't belong to institutions.
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Make school_id nullable in classrooms table
    op.alter_column('classrooms', 'school_id',
                    existing_type=sa.String(),
                    nullable=True)

def downgrade():
    # Make school_id not nullable again (will fail if there are NULL values)
    op.alter_column('classrooms', 'school_id',
                    existing_type=sa.String(),
                    nullable=False)