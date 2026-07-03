"""Add current_ctc, expected_ctc, notice_period, working_status to candidates."""

import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


COMPENSATION_COLS = [
    ("current_ctc", sa.String(100)),
    ("expected_ctc", sa.String(100)),
    ("notice_period", sa.String(100)),
    ("working_status", sa.String(30)),
]


def upgrade() -> None:
    for table in ("candidates_staging", "candidates_main"):
        for name, col_type in COMPENSATION_COLS:
            op.add_column(table, sa.Column(name, col_type, nullable=True))


def downgrade() -> None:
    for table in ("candidates_main", "candidates_staging"):
        for name, _ in COMPENSATION_COLS:
            op.drop_column(table, name)
