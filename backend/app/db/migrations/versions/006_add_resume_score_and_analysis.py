"""Add resume_overall_score + resume_analysis columns to candidates."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("candidates_staging", "candidates_main"):
        op.add_column(table, sa.Column("resume_overall_score", sa.Float(), nullable=True))
        op.add_column(table, sa.Column("resume_analysis", JSONB, nullable=True))
        op.create_index(
            f"ix_{table}_resume_overall_score",
            table,
            ["resume_overall_score"],
        )


def downgrade() -> None:
    for table in ("candidates_main", "candidates_staging"):
        op.drop_index(f"ix_{table}_resume_overall_score", table_name=table)
        op.drop_column(table, "resume_analysis")
        op.drop_column(table, "resume_overall_score")
