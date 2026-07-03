"""CRUD operations for Verification."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.verification import Verification


async def create_verification(
    db: AsyncSession,
    candidate_id: str,
    doc_type: str,
    document_id: str,
) -> Verification:
    verification = Verification(
        verification_ref=f"VER-{uuid.uuid4().hex[:8].upper()}",
        candidate_id=candidate_id,
        verification_type="IDENTITY",
        document_type=doc_type,
        document_id=document_id,
        status="PENDING",
    )
    db.add(verification)
    await db.flush()
    await db.refresh(verification)
    return verification


async def update_verification(
    db: AsyncSession, verification_id: str, **kwargs
) -> Verification:
    result = await db.execute(
        select(Verification).where(Verification.id == verification_id)
    )
    verification = result.scalar_one_or_none()
    if verification is None:
        raise ValueError(f"Verification {verification_id!r} not found")
    for key, value in kwargs.items():
        setattr(verification, key, value)
    await db.flush()
    await db.refresh(verification)
    return verification


async def get_verifications_for_candidate(
    db: AsyncSession, candidate_id: str
) -> list[Verification]:
    """Return all verification records for a candidate, newest first."""
    rows = await db.execute(
        select(Verification)
        .where(Verification.candidate_id == candidate_id)
        .order_by(Verification.created_at.desc())
    )
    return list(rows.scalars().all())


async def get_verified_doc_types(db: AsyncSession, candidate_id: str) -> set[str]:
    """Return the set of doc_types this candidate has successfully verified."""
    rows = await db.execute(
        select(Verification.document_type)
        .where(Verification.candidate_id == candidate_id)
        .where(Verification.status == "VERIFIED")
    )
    return {r[0] for r in rows.all()}
