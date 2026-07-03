"""Business logic for candidate registration and agent task creation."""

import random
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import task_repository
from app.schemas.requests.candidate import RegisterCandidateRequest
from app.repositories import candidate_repository


def _generate_candidate_ref() -> str:
    year = datetime.now().year
    suffix = str(random.randint(0, 99999)).zfill(5)
    return f"SR-{year}-{suffix}"


async def register_candidate(
    db: AsyncSession,
    data: RegisterCandidateRequest,
) -> dict:
    """Create a new candidate staging record and return ref + status."""
    candidate_ref = _generate_candidate_ref()
    staging = await candidate_repository.create_staging(
        db,
        {
            "candidate_ref": candidate_ref,
            "full_name": data.full_name,
            "email": data.email,
            "phone": data.phone,
            "target_role": data.target_role,
            "current_ctc": data.current_ctc,
            "expected_ctc": data.expected_ctc,
            "notice_period": data.notice_period,
            "working_status": data.working_status,
            "location": data.location,
            "preferred_location": data.preferred_location,
            "status": "PENDING",
        },
    )
    await db.commit()
    return {"candidate_ref": staging.candidate_ref, "status": staging.status}


async def create_agent_task(
    db: AsyncSession,
    task_type: str,
    reference_id: str,
) -> str:
    """Create a background_task record and return task_id (str)."""
    task = await task_repository.create_task(db, task_type, reference_id)
    await db.commit()
    return str(task.id)
