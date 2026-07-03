"""Add preferred_location column to candidates."""

import sqlalchemy as sa
from alembic import op

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("candidates_staging", "candidates_main"):
        op.add_column(table, sa.Column("preferred_location", sa.String(255), nullable=True))


def downgrade() -> None:
    for table in ("candidates_main", "candidates_staging"):
        op.drop_column(table, "preferred_location")
