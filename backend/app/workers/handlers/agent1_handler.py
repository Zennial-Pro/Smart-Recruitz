"""ARQ handler for Agent 1: Resume Parser."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.agent1_resume_parser import parse_resume
from app.db.session import async_session_factory
from app.repositories import task_repository
from app.repositories.candidate_repository import get_staging_by_ref, update_staging
from app.repositories.document_repository import create_document


async def run_agent1(
    task_id: str,
    candidate_ref: str,
    file_path: str,
    filename: str,
    content_type: str,
    file_size_bytes: int,
) -> None:
    async with async_session_factory() as db:
        await task_repository.mark_processing(db, task_id)
        await db.commit()

        try:
            # Save document record
            doc = await create_document(
                db,
                filename=filename,
                storage_path=file_path,
                content_type=content_type,
                file_size_bytes=file_size_bytes,
                document_category="RESUME",
                uploaded_by_ref=candidate_ref,
            )
            await db.commit()

            # Run agent
            result = await parse_resume(file_path, content_type)
            result_dict = result.model_dump()

            # Update staging record — preserve entered full_name/email/phone as source of truth.
            # Resume-parsed name is kept in raw_resume_data for cross-checking during ID verification.
            staging = await get_staging_by_ref(db, candidate_ref)
            if staging:
                update_kwargs = dict(
                    current_title=result.current_title,
                    total_experience_years=result.total_experience_years,
                    primary_domain=result.primary_domain,
                    parse_confidence=result.confidence_score,
                    raw_resume_data=result_dict,
                    skills_normalized=[s.model_dump() for s in result.skills_normalized],
                    experience=[e.model_dump() for e in result.experience],
                    education=[ed.model_dump() for ed in result.education],
                    resume_document_id=doc.id,
                    resume_overall_score=float(result.analysis.overall_score),
                    resume_analysis=result.analysis.model_dump(),
                )
                # Only persist parsed URLs if not already set by the candidate
                # (candidate-entered values take precedence)
                if not staging.github_url and result.github_url:
                    update_kwargs["github_url"] = result.github_url
                if not staging.linkedin_url and result.linkedin_url:
                    update_kwargs["linkedin_url"] = result.linkedin_url
                await update_staging(db, candidate_ref, **update_kwargs)
            await db.commit()

            await task_repository.mark_completed(db, task_id, result_dict)
            await db.commit()

        except Exception as exc:
            await db.rollback()
            async with async_session_factory() as err_db:
                await task_repository.mark_failed(err_db, task_id, str(exc))
                await err_db.commit()
            raise
