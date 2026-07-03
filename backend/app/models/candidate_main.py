"""Candidates main model — verified candidates with normalized relations."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin


class CandidateMain(TimestampMixin, Base):
    __tablename__ = "lms_recruit_candidates_main"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    candidate_ref: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="VERIFIED")
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    current_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    total_experience_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    primary_domain: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_ctc: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expected_ctc: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notice_period: Mapped[str | None] = mapped_column(String(100), nullable=True)
    working_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    preferred_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    linkedin_cross_check: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    resume_overall_score: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    resume_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    readiness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="PENDING"
    )
    talent_pool_entry_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    raw_profile_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    reinterview_allowed: Mapped[bool] = mapped_column(nullable=False, default=False)

    # Relationships
    skills = relationship("CandidateSkill", back_populates="candidate", lazy="selectin")
    experiences = relationship(
        "CandidateExperience", back_populates="candidate", lazy="selectin"
    )
    educations = relationship(
        "CandidateEducation", back_populates="candidate", lazy="selectin"
    )
    verifications = relationship("Verification", back_populates="candidate", lazy="selectin")
    interviews = relationship("Interview", back_populates="candidate", lazy="selectin")

    # pg_trgm index for fuzzy name search (Agent 2)
    __table_args__ = (
        Index(
            "ix_candidates_main_full_name_trgm",
            "full_name",
            postgresql_using="gin",
            postgresql_ops={"full_name": "gin_trgm_ops"},
        ),
    )
