"""Add tax_id column to organizations table

Revision ID: f8a7c3d2e1b0
Revises: ed63e979dc1c
Create Date: 2026-01-10 14:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f8a7c3d2e1b0"
down_revision = "ed63e979dc1c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add tax_id column to organizations table
    # Nullable initially to support existing data
    op.add_column(
        "organizations",
        sa.Column("tax_id", sa.String(20), nullable=True),
    )

    # Create unique constraint on tax_id
    op.create_unique_constraint(
        "uq_organizations_tax_id",
        "organizations",
        ["tax_id"],
    )

    # Create index for faster lookups
    op.create_index(
        "ix_organizations_tax_id",
        "organizations",
        ["tax_id"],
    )


def downgrade() -> None:
    # Remove index
    op.drop_index("ix_organizations_tax_id", table_name="organizations")

    # Remove unique constraint
    op.drop_constraint("uq_organizations_tax_id", "organizations", type_="unique")

    # Remove column
    op.drop_column("organizations", "tax_id")
