"""ARQ handler for Agent 2: Duplicate Detector."""

from app.agents.agent2_duplicate_detector import check_duplicate
from app.db.session import async_session_factory
from app.repositories import task_repository
from app.repositories.candidate_repository import (
    get_candidates_for_duplicate_check,
    get_staging_by_ref,
    update_staging,
)


async def run_agent2(task_id: str, candidate_ref: str) -> None:
    async with async_session_factory() as db:
        await task_repository.mark_processing(db, task_id)
        await db.commit()

        try:
            staging = await get_staging_by_ref(db, candidate_ref)
            if not staging:
                raise ValueError(f"Staging candidate {candidate_ref!r} not found")

            # Fetch potential duplicates via pg_trgm
            matches = await get_candidates_for_duplicate_check(
                db,
                full_name=staging.full_name,
                email=staging.email,
                phone=staging.phone,
            )

            candidate_data = {
                "full_name": staging.full_name,
                "email": staging.email,
                "phone": staging.phone,
            }
            matches_data = [
                {
                    "candidate_ref": m.candidate_ref,
                    "full_name": m.full_name,
                    "email": m.email,
                    "phone": m.phone,
                }
                for m in matches
            ]

            result = await check_duplicate(candidate_data, matches_data)
            result_dict = result.model_dump()

            # Update staging status
            new_status = {
                "UNIQUE": "COMPLETED",
                "DUPLICATE": "REJECTED",
                "UNCERTAIN": "DUPLICATE_REVIEW",
            }.get(result.result, "DUPLICATE_REVIEW")

            await update_staging(
                db,
                candidate_ref,
                status=new_status,
                duplicate_pre_check=result_dict,
            )
            await db.commit()

            await task_repository.mark_completed(db, task_id, result_dict)
            await db.commit()

        except Exception as exc:
            await db.rollback()
            async with async_session_factory() as err_db:
                await task_repository.mark_failed(err_db, task_id, str(exc))
                await err_db.commit()
            raise
