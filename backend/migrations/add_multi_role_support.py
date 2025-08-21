"""Add multi-role support to users table

This migration adds columns to support users with multiple role contexts
(individual teacher and institutional admin).
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add multi-role support columns
    op.add_column('users', sa.Column('is_individual_teacher', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('is_institutional_admin', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('current_role_context', sa.String(), nullable=True))
    
    # Set default values for existing records
    op.execute("UPDATE users SET is_individual_teacher = false WHERE is_individual_teacher IS NULL")
    op.execute("UPDATE users SET is_institutional_admin = false WHERE is_institutional_admin IS NULL")
    op.execute("UPDATE users SET current_role_context = 'default' WHERE current_role_context IS NULL")
    
    # Make columns not nullable after setting defaults
    op.alter_column('users', 'is_individual_teacher', nullable=False)
    op.alter_column('users', 'is_institutional_admin', nullable=False)

def downgrade():
    # Remove multi-role support columns
    op.drop_column('users', 'current_role_context')
    op.drop_column('users', 'is_institutional_admin')
    op.drop_column('users', 'is_individual_teacher')