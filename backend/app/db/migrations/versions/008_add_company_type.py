"""Add company_type to candidate_experiences."""

import sqlalchemy as sa
from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "candidate_experiences",
        sa.Column("company_type", sa.String(20), nullable=True),
    )
    op.create_index(
        "ix_candidate_experiences_company_type",
        "candidate_experiences",
        ["company_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_candidate_experiences_company_type", table_name="candidate_experiences")
    op.drop_column("candidate_experiences", "company_type")
