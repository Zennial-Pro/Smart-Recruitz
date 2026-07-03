"""Interviews model — interview sessions with scores."""

import uuid

from sqlalchemy import Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin


class Interview(TimestampMixin, Base):
    __tablename__ = "lms_recruit_interviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    interview_ref: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("application.lms_recruit_candidates_main.id", ondelete="CASCADE"),
        nullable=False,
    )
    interview_type: Mapped[str] = mapped_column(String(20), nullable=False, default="L1_SCREENING")
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="QUESTIONS_GENERATED"
    )
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Outbound voice-interview call (Zingaro). voice_call_id correlates the
    # platform's call to this interview; call_status tracks its lifecycle.
    voice_call_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    call_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    l1_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    recommendation: Mapped[str | None] = mapped_column(String(30), nullable=True)
    evaluation_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    interviewer_guide: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    candidate = relationship("CandidateMain", back_populates="interviews")
    questions = relationship("InterviewQuestion", back_populates="interview", lazy="selectin")
