"""Candidates staging model — temporary raw data from Agent 1."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin


class CandidateStaging(TimestampMixin, Base):
    __tablename__ = "lms_recruit_candidates_staging"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    candidate_ref: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    current_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_ctc: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expected_ctc: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notice_period: Mapped[str | None] = mapped_column(String(100), nullable=True)
    working_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferred_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    linkedin_cross_check: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    resume_overall_score: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    resume_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # JSONB columns — flexible AI output storage
    raw_resume_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    skills_normalized: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    experience: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    education: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    certifications: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    projects: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    languages: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    domain_experience: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    duplicate_pre_check: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Parsed fields
    total_experience_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    primary_domain: Mapped[str | None] = mapped_column(String(100), nullable=True)
    parse_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # FK to uploaded resume
    resume_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("application.lms_recruit_uploaded_documents.id", ondelete="SET NULL"),
        nullable=True,
    )
