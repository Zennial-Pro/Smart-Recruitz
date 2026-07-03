"""Candidate skills model — skill proficiency mapping."""

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CandidateSkill(Base):
    __tablename__ = "lms_recruit_candidate_skills"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("application.lms_recruit_candidates_main.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("application.lms_recruit_skill_taxonomy.id", ondelete="CASCADE"),
        nullable=False,
    )
    proficiency: Mapped[str] = mapped_column(String(20), nullable=False)
    years_experience: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_implied: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    candidate = relationship("CandidateMain", back_populates="skills")
    skill = relationship("SkillTaxonomy", lazy="selectin")
