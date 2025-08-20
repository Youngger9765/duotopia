"""rename_class_to_classroom

Revision ID: af563d6729f2
Revises: e0055dfe140b
Create Date: 2025-08-20 10:49:18.558541

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af563d6729f2'
down_revision: Union[str, None] = 'e0055dfe140b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename tables
    op.rename_table('classes', 'classrooms')
    op.rename_table('class_students', 'classroom_students')
    op.rename_table('class_course_mappings', 'classroom_course_mappings')
    
    # Rename foreign key columns
    with op.batch_alter_table('classroom_students') as batch_op:
        batch_op.alter_column('class_id', new_column_name='classroom_id')
    
    with op.batch_alter_table('classroom_course_mappings') as batch_op:
        batch_op.alter_column('class_id', new_column_name='classroom_id')


def downgrade() -> None:
    # Rename foreign key columns back
    with op.batch_alter_table('classroom_course_mappings') as batch_op:
        batch_op.alter_column('classroom_id', new_column_name='class_id')
    
    with op.batch_alter_table('classroom_students') as batch_op:
        batch_op.alter_column('classroom_id', new_column_name='class_id')
    
    # Rename tables back
    op.rename_table('classroom_course_mappings', 'class_course_mappings')
    op.rename_table('classroom_students', 'class_students')
    op.rename_table('classrooms', 'classes')
