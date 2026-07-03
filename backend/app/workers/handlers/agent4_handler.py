"""ARQ handler for Agent 4: Interview Question Generator."""

from app.agents.agent4_question_generator import generate_questions
from app.db.session import async_session_factory
from app.repositories import task_repository
from app.repositories.candidate_repository import get_main_by_ref, get_staging_by_ref
from app.repositories.interview_repository import create_interview, create_questions, get_previous_questions


async def run_agent4(task_id: str, candidate_ref: str) -> None:
    async with async_session_factory() as db:
        await task_repository.mark_processing(db, task_id)
        await db.commit()

        try:
            # Build candidate profile from main (preferred) or staging
            main = await get_main_by_ref(db, candidate_ref)
            staging = await get_staging_by_ref(db, candidate_ref)

            candidate_profile: dict = {}
            if main:
                candidate_profile = {
                    "full_name": main.full_name,
                    "current_title": main.current_title,
                    "total_experience_years": main.total_experience_years,
                    "primary_domain": main.primary_domain,
                    "target_role": main.target_role,
                    "skills": main.raw_profile_data.get("skills_normalized", []) if main.raw_profile_data else [],
                    "experience": main.raw_profile_data.get("experience", []) if main.raw_profile_data else [],
                }
            elif staging:
                candidate_profile = {
                    "full_name": staging.full_name,
                    "current_title": staging.current_title,
                    "total_experience_years": staging.total_experience_years,
                    "primary_domain": staging.primary_domain,
                    "target_role": staging.current_title,
                    "skills": staging.skills_normalized or [],
                    "experience": staging.experience or [],
                }
            else:
                raise ValueError(f"Candidate {candidate_ref!r} not found")

            # Fetch previously asked questions to avoid repetition
            candidate_id = str(main.id) if main else None
            if candidate_id is None:
                raise ValueError("CandidateMain record required for interview generation")

            previous_questions = await get_previous_questions(db, candidate_id)

            # Run agent
            result = await generate_questions(candidate_profile, previous_questions)

            interview = await create_interview(db, candidate_id)

            questions_data = [q.model_dump() for q in result.questions]
            await create_questions(db, str(interview.id), questions_data)
            await db.commit()

            result_dict = {
                "interview_ref": interview.interview_ref,
                "questions": questions_data,
            }

            await task_repository.mark_completed(db, task_id, result_dict)
            await db.commit()

        except Exception as exc:
            await db.rollback()
            async with async_session_factory() as err_db:
                await task_repository.mark_failed(err_db, task_id, str(exc))
                await err_db.commit()
            raise
