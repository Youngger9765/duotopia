"""add_email_verification_and_remove_unique_constraint

Revision ID: 47e26e8bf64b
Revises: fec3ec42ce70
Create Date: 2025-09-06 22:37:51.588147

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "47e26e8bf64b"
down_revision: Union[str, None] = "fec3ec42ce70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add email verification fields if they don't exist
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='students' AND column_name='email_verified'"
        )
    )
    if not result.fetchone():
        op.add_column(
            "students",
            sa.Column("email_verified", sa.Boolean(), nullable=True, default=False),
        )

    result = conn.execute(
        sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='students' AND column_name='email_verified_at'"
        )
    )
    if not result.fetchone():
        op.add_column(
            "students",
            sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        )

    result = conn.execute(
        sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='students' AND column_name='email_verification_token'"
        )
    )
    if not result.fetchone():
        op.add_column(
            "students",
            sa.Column("email_verification_token", sa.String(length=100), nullable=True),
        )

    result = conn.execute(
        sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='students' AND column_name='email_verification_sent_at'"
        )
    )
    if not result.fetchone():
        op.add_column(
            "students",
            sa.Column(
                "email_verification_sent_at", sa.DateTime(timezone=True), nullable=True
            ),
        )

    # Remove parent_email column if it exists
    op.execute("ALTER TABLE students DROP COLUMN IF EXISTS parent_email")

    # Remove unique constraint from email and create non-unique index
    # First check if index exists
    result = conn.execute(
        sa.text(
            "SELECT indexname FROM pg_indexes WHERE tablename='students' AND indexname='ix_students_email'"
        )
    )
    if result.fetchone():
        op.drop_index("ix_students_email", table_name="students")
    op.create_index(op.f("ix_students_email"), "students", ["email"], unique=False)


def downgrade() -> None:
    # Restore unique constraint on email
    op.drop_index(op.f("ix_students_email"), table_name="students")
    op.create_index("ix_students_email", "students", ["email"], unique=True)

    # Add back parent_email column
    op.add_column(
        "students",
        sa.Column(
            "parent_email", sa.VARCHAR(length=255), autoincrement=False, nullable=True
        ),
    )

    # SAFE: Remove email verification fields - these were never used in production
    op.drop_column("students", "email_verification_sent_at")
    op.drop_column("students", "email_verification_token")
    op.drop_column("students", "email_verified_at")
    op.drop_column("students", "email_verified")
