"""Candidate experiences model — work history."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CandidateExperience(Base):
    __tablename__ = "lms_recruit_candidate_experiences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("application.lms_recruit_candidates_main.id", ondelete="CASCADE"),
        nullable=False,
    )
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    duration_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    domain: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # PRODUCT | SERVICE | GCC | STARTUP | OTHER — classified by Agent 1
    company_type: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    responsibilities: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    candidate = relationship("CandidateMain", back_populates="experiences")
