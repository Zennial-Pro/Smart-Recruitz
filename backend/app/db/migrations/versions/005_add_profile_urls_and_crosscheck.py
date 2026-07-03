"""Add github_url, linkedin_url, linkedin_cross_check to candidates."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("candidates_staging", "candidates_main"):
        op.add_column(table, sa.Column("github_url", sa.String(500), nullable=True))
        op.add_column(table, sa.Column("linkedin_url", sa.String(500), nullable=True))
        op.add_column(table, sa.Column("linkedin_cross_check", JSONB, nullable=True))


def downgrade() -> None:
    for table in ("candidates_main", "candidates_staging"):
        op.drop_column(table, "linkedin_cross_check")
        op.drop_column(table, "linkedin_url")
        op.drop_column(table, "github_url")
