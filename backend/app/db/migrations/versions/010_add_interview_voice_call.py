"""Add voice_call_id + call_status to interviews (outbound voice interview).

NOTE on table name: migrations 001–009 reference bare names (e.g. "interviews"),
but the live database holds the schema-qualified, prefixed tables
(application.lms_recruit_interviews) — the models carry MetaData(schema="application")
and the lms_recruit_ prefix, and the DB was built from the models then stamped to
009 (the bare-name migrations never actually ran against it). This migration
therefore targets the REAL table: application.lms_recruit_interviews. Since alembic
is at 009, `upgrade head` runs only this revision.
"""

import sqlalchemy as sa
from alembic import op

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None

_TABLE = "lms_recruit_interviews"
_SCHEMA = "application"


def upgrade() -> None:
    op.add_column(_TABLE, sa.Column("voice_call_id", sa.String(64), nullable=True), schema=_SCHEMA)
    op.add_column(_TABLE, sa.Column("call_status", sa.String(30), nullable=True), schema=_SCHEMA)
    op.create_index(
        "ix_lms_recruit_interviews_voice_call_id",
        _TABLE,
        ["voice_call_id"],
        schema=_SCHEMA,
    )


def downgrade() -> None:
    op.drop_index("ix_lms_recruit_interviews_voice_call_id", table_name=_TABLE, schema=_SCHEMA)
    op.drop_column(_TABLE, "call_status", schema=_SCHEMA)
    op.drop_column(_TABLE, "voice_call_id", schema=_SCHEMA)
