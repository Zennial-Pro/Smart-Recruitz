"""Add video_url to interviews."""

import sqlalchemy as sa
from alembic import op

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("interviews", sa.Column("video_url", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("interviews", "video_url")
