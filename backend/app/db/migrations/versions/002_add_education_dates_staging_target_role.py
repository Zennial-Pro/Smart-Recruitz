"""Add education start/end dates and target_role to candidates_staging.

Revision ID: 002_education_dates
Revises: 001_initial
Create Date: 2026-04-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_education_dates"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("candidate_educations", sa.Column("start_date", sa.String(20), nullable=True))
    op.add_column("candidate_educations", sa.Column("end_date", sa.String(20), nullable=True))
    op.add_column("candidates_staging", sa.Column("target_role", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("candidate_educations", "start_date")
    op.drop_column("candidate_educations", "end_date")
    op.drop_column("candidates_staging", "target_role")
