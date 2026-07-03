"""Skill taxonomy model — master skill list with hierarchy."""

import uuid

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SkillTaxonomy(Base):
    __tablename__ = "lms_recruit_skill_taxonomy"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    standard_name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    aliases: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    parent_skill_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("application.lms_recruit_skill_taxonomy.id", ondelete="SET NULL"),
        nullable=True,
    )

    parent = relationship("SkillTaxonomy", remote_side="SkillTaxonomy.id", lazy="selectin")
