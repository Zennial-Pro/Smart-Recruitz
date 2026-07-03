"""Interview questions model — generated questions with expected answers."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class InterviewQuestion(Base):
    __tablename__ = "lms_recruit_interview_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("application.lms_recruit_interviews.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_ref: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    targets_skill: Mapped[str | None] = mapped_column(String(100), nullable=True)
    targets_experience: Mapped[str | None] = mapped_column(String(255), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    expected_answer_points: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    follow_up_questions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    time_estimate_mins: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Set by Agent 5 after scoring
    answer_quality: Mapped[str | None] = mapped_column(String(20), nullable=True)
    answer_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    question_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    interview = relationship("Interview", back_populates="questions")
