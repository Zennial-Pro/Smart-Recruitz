"""Background handler for LinkedIn x Resume cross-check."""

import structlog

from app.agents.agent_consistency_check import cross_check_linkedin
from app.core.clients.coresignal_client import LinkedInLookupError, fetch_linkedin_profile
from app.db.session import async_session_factory
from app.repositories import task_repository
from app.repositories.candidate_repository import get_staging_by_ref, update_staging

logger = structlog.get_logger(__name__)


async def run_consistency_check(task_id: str, candidate_ref: str) -> None:
    async with async_session_factory() as db:
        await task_repository.mark_processing(db, task_id)
        await db.commit()

        try:
            staging = await get_staging_by_ref(db, candidate_ref)
            if not staging:
                raise ValueError(f"Staging candidate {candidate_ref!r} not found")
            if not staging.linkedin_url:
                raise ValueError("No LinkedIn URL on candidate; cannot run cross-check")

            # 1) Fetch LinkedIn profile via Coresignal
            try:
                linkedin_profile = await fetch_linkedin_profile(staging.linkedin_url)
            except LinkedInLookupError as exc:
                logger.warning("consistency.linkedin_lookup_failed", error=str(exc), candidate_ref=candidate_ref)
                linkedin_profile = None

            # 2) LLM diff vs resume experience
            resume_experiences = staging.experience or []
            result = await cross_check_linkedin(resume_experiences, linkedin_profile)
            result_dict = result.model_dump()

            # 3) Persist on staging
            await update_staging(db, candidate_ref, linkedin_cross_check=result_dict)
            await db.commit()

            await task_repository.mark_completed(db, task_id, result_dict)
            await db.commit()

        except Exception as exc:
            await db.rollback()
            async with async_session_factory() as err_db:
                await task_repository.mark_failed(err_db, task_id, str(exc))
                await err_db.commit()
            raise
