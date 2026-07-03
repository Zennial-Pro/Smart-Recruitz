"""Handler for Agent 5: Interview Scorer.

Agents run via FastAPI BackgroundTasks (no separate worker process).

The scoring core is factored into ``score_and_update`` so both the text-transcript
path (``run_agent5``) and the voice-call path (``run_voice_postcall``) score and
transition the candidate through one source of truth.
"""

from app.agents.agent5_interview_scorer import score_interview
from app.db.session import async_session_factory
from app.models.interview import Interview
from app.repositories import task_repository
from app.repositories.candidate_repository import get_main_by_ref, update_main
from app.repositories.interview_repository import (
    get_interview_with_questions,
    update_interview_scores,
)


async def score_and_update(
    db,
    interview: Interview,
    candidate_ref: str,
    transcript: str,
) -> dict:
    """Score a transcript against the interview's questions and transition the candidate.

    Persists scores + transcript on the interview, then flips the candidate to
    TALENT_POOL (PASSED) or INTERVIEW_FAILED. Returns the scoring result dict.
    Caller owns the transaction (commit / rollback).
    """
    questions_data = [
        {
            "q_id": q.question_ref,
            "question": q.question_text,
            "category": q.category,
            "expected_answer_points": q.expected_answer_points or [],
        }
        for q in interview.questions
    ]

    result = await score_interview(transcript, questions_data)
    result_dict = result.model_dump()

    # Persist scores + the raw transcript so hiring managers can review it
    await update_interview_scores(db, str(interview.id), result_dict, transcript=transcript)

    # Update candidate status
    main = await get_main_by_ref(db, candidate_ref)
    if main:
        new_status = "TALENT_POOL" if result.l1_status == "PASSED" else "INTERVIEW_FAILED"
        await update_main(
            db,
            candidate_ref,
            status=new_status,
            readiness_score=result.overall_score,
        )

    return result_dict


async def run_agent5(
    task_id: str,
    candidate_ref: str,
    interview_ref: str,
    transcript: str,
) -> None:
    async with async_session_factory() as db:
        await task_repository.mark_processing(db, task_id)
        await db.commit()

        try:
            interview = await get_interview_with_questions(db, interview_ref)
            if not interview:
                raise ValueError(f"Interview {interview_ref!r} not found")

            result_dict = await score_and_update(db, interview, candidate_ref, transcript)

            await db.commit()

            await task_repository.mark_completed(db, task_id, result_dict)
            await db.commit()

        except Exception as exc:
            await db.rollback()
            async with async_session_factory() as err_db:
                await task_repository.mark_failed(err_db, task_id, str(exc))
                await err_db.commit()
            raise
