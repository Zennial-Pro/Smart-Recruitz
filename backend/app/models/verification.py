"""Verifications model — Agent 3 ID verification results."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Verification(Base):
    __tablename__ = "lms_recruit_verifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    verification_ref: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("application.lms_recruit_candidates_main.id", ondelete="CASCADE"),
        nullable=False,
    )
    verification_type: Mapped[str] = mapped_column(String(20), nullable=False, default="IDENTITY")
    document_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    extracted_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    data_match_results: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    document_authenticity: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    flags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("application.lms_recruit_uploaded_documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    candidate = relationship("CandidateMain", back_populates="verifications")
