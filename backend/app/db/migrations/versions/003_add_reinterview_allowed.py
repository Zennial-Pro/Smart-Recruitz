"""Add reinterview_allowed to candidates_main."""

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002_education_dates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "candidates_main",
        sa.Column("reinterview_allowed", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("candidates_main", "reinterview_allowed")
