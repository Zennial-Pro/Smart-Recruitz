"""Candidate registration endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.candidate_main import CandidateMain
from app.models.candidate_staging import CandidateStaging
from app.models.interview import Interview
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clients.openai_client import chat_completion
from app.db.session import get_db_session
from app.repositories.verification_repository import (
    get_verifications_for_candidate,
    get_verified_doc_types,
)
from app.schemas.requests.candidate import RegisterCandidateRequest
from app.schemas.responses.candidate import CandidateRegisteredResponse
from app.services.candidate_service import register_candidate

router = APIRouter(prefix="/candidates", tags=["Candidates"])


class ValidateNameRequest(BaseModel):
    name: str


@router.post("/validate-name")
async def validate_name(data: ValidateNameRequest) -> dict:
    result = await chat_completion(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a name validator. Determine if the input is a real human full name. "
                    "Return JSON: {\"valid\": true/false, \"reason\": \"one line explanation\"}. "
                    "Valid names contain only letters, spaces, hyphens, apostrophes. "
                    "Reject gibberish, profanity, misspelled profanity, celebrity/fictional names used sarcastically, single words, or anything that is clearly not a real person's name."
                ),
            },
            {"role": "user", "content": data.name},
        ],
        model="gpt-4o-mini",
    )
    return {"valid": bool(result.get("valid")), "reason": result.get("reason", "")}


@router.get("/{candidate_ref}/status")
async def get_status(
    candidate_ref: str,
    db: AsyncSession = Depends(get_db_session),
):
    row = await db.execute(
        select(CandidateMain.reinterview_allowed)
        .where(CandidateMain.candidate_ref == candidate_ref)
    )
    result = row.scalar_one_or_none()
    if result is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {"reinterview_allowed": result}


MANDATORY_ID_DOC_TYPES = ["AADHAAR_CARD", "PAN_CARD"]
OPTIONAL_ID_DOC_TYPES = ["PASSPORT"]


@router.get("/{candidate_ref}/verifications")
async def get_verifications(
    candidate_ref: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Return ID-verification progress so the frontend can decide what to ask next."""
    row = await db.execute(
        select(CandidateMain.id).where(CandidateMain.candidate_ref == candidate_ref)
    )
    main_id = row.scalar_one_or_none()
    if main_id is None:
        # Candidate has not yet been promoted to main (no ID uploaded yet)
        return {
            "verified_doc_types": [],
            "all_mandatory_verified": False,
            "mandatory_doc_types": MANDATORY_ID_DOC_TYPES,
            "optional_doc_types": OPTIONAL_ID_DOC_TYPES,
            "verifications": [],
        }

    verifications = await get_verifications_for_candidate(db, str(main_id))
    verified = await get_verified_doc_types(db, str(main_id))

    return {
        "verified_doc_types": sorted(verified),
        "all_mandatory_verified": set(MANDATORY_ID_DOC_TYPES).issubset(verified),
        "mandatory_doc_types": MANDATORY_ID_DOC_TYPES,
        "optional_doc_types": OPTIONAL_ID_DOC_TYPES,
        "verifications": [
            {
                "verification_ref": v.verification_ref,
                "document_type": v.document_type,
                "status": v.status,
                "confidence_score": v.confidence_score,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in verifications
        ],
    }


class LookupRequest(BaseModel):
    email: str


@router.post("/lookup")
async def lookup_candidate(
    data: LookupRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Find a candidate by email and return their ref + latest interview result."""
    row = await db.execute(
        select(CandidateMain).where(CandidateMain.email == data.email.lower().strip())
    )
    candidate = row.scalar_one_or_none()

    if not candidate:
        # Also check staging (registered but not yet through duplicate check)
        staging_row = await db.execute(
            select(CandidateStaging).where(CandidateStaging.email == data.email.lower().strip())
        )
        staging = staging_row.scalar_one_or_none()
        if staging:
            return {
                "found": True,
                "candidate_ref": staging.candidate_ref,
                "full_name": staging.full_name,
                "stage": "registered",
                "scoring_result": None,
                "reinterview_allowed": False,
            }
        return {"found": False}

    # Get latest scored interview
    interview_row = await db.execute(
        select(Interview)
        .where(Interview.candidate_id == candidate.id)
        .where(Interview.status == "SCORED")
        .order_by(Interview.created_at.desc())
        .limit(1)
    )
    interview = interview_row.scalar_one_or_none()

    # Determine real stage based on verification progress.
    # A main row exists from the first ID upload, but the candidate isn't
    # truly "id_verified" until all mandatory docs are done.
    verified = await get_verified_doc_types(db, str(candidate.id))
    all_mandatory = set(MANDATORY_ID_DOC_TYPES).issubset(verified)
    if interview:
        stage = "completed"
    elif all_mandatory:
        stage = "id_verified"
    else:
        stage = "id_partial"

    return {
        "found": True,
        "candidate_ref": candidate.candidate_ref,
        "full_name": candidate.full_name,
        "stage": stage,
        "verified_doc_types": sorted(verified),
        "scoring_result": interview.evaluation_data if interview else None,
        "reinterview_allowed": candidate.reinterview_allowed,
    }


@router.post("/register", response_model=CandidateRegisteredResponse, status_code=201)
async def register(
    data: RegisterCandidateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> CandidateRegisteredResponse:
    result = await register_candidate(db, data)
    return CandidateRegisteredResponse(**result)
