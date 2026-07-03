"""CRUD operations for Interview and InterviewQuestion."""

import uuid

from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config.constants import InterviewStatus
from app.models.interview import Interview
from app.models.interview_question import InterviewQuestion


async def create_interview(db: AsyncSession, candidate_id: str) -> Interview:
    interview = Interview(
        interview_ref=f"INT-{uuid.uuid4().hex[:8].upper()}",
        candidate_id=candidate_id,
        interview_type="L1_SCREENING",
        status="QUESTIONS_GENERATED",
    )
    db.add(interview)
    await db.flush()
    await db.refresh(interview)
    return interview


async def create_questions(
    db: AsyncSession, interview_id: str, questions: list[dict]
) -> list[InterviewQuestion]:
    records: list[InterviewQuestion] = []
    for q in questions:
        record = InterviewQuestion(
            interview_id=interview_id,
            question_ref=q.get("q_id", ""),
            category=q.get("category", ""),
            question_text=q.get("question", ""),
            targets_skill=q.get("targets_skill", ""),
            difficulty=q.get("difficulty", "MID"),
            expected_answer_points=q.get("expected_answer_points", []),
            time_estimate_mins=q.get("time_estimate_mins", 5),
        )
        db.add(record)
        records.append(record)
    await db.flush()
    return records


async def get_previous_questions(
    db: AsyncSession, candidate_id: str
) -> list[str]:
    """Return all question texts asked to this candidate in past interviews."""
    result = await db.execute(
        select(InterviewQuestion.question_text)
        .join(Interview, Interview.id == InterviewQuestion.interview_id)
        .where(Interview.candidate_id == candidate_id)
    )
    return [row[0] for row in result.fetchall()]


async def get_interview_with_questions(
    db: AsyncSession, interview_ref: str
) -> Interview | None:
    result = await db.execute(
        select(Interview)
        .where(Interview.interview_ref == interview_ref)
        .options(selectinload(Interview.questions))
    )
    return result.scalar_one_or_none()


async def get_active_interview_by_candidate_id(
    db: AsyncSession, candidate_id: str
) -> Interview | None:
    """Latest interview awaiting a voice call for this candidate, with questions.

    Used by the pre-call webhook, which can only identify the candidate by phone.
    Prefers an interview already CALL_IN_PROGRESS (the normal path after initiate),
    then falls back to QUESTIONS_GENERATED (covers a manually-triggered dial),
    newest first.
    """
    status_priority = case(
        (Interview.status == InterviewStatus.CALL_IN_PROGRESS, 0),
        (Interview.status == InterviewStatus.QUESTIONS_GENERATED, 1),
        else_=2,
    )
    result = await db.execute(
        select(Interview)
        .where(
            Interview.candidate_id == candidate_id,
            Interview.status.in_(
                [InterviewStatus.CALL_IN_PROGRESS, InterviewStatus.QUESTIONS_GENERATED]
            ),
        )
        .options(selectinload(Interview.questions))
        .order_by(status_priority, Interview.created_at.desc())
    )
    return result.scalars().first()


async def get_interview_by_call_id(
    db: AsyncSession, call_id: str
) -> Interview | None:
    """Find the interview correlated to a Zingaro call_id, with questions."""
    result = await db.execute(
        select(Interview)
        .where(Interview.voice_call_id == call_id)
        .options(selectinload(Interview.questions))
    )
    return result.scalar_one_or_none()


async def get_latest_in_progress_interview(db: AsyncSession) -> Interview | None:
    """Most recent interview currently CALL_IN_PROGRESS, with questions.

    Last-resort correlation for post-call webhooks that carry no usable
    identifier (the direct-ai-call post-call sends an empty phone, doesn't echo
    our metadata, and its session_id differs from the placed call's id). Reliable
    when calls happen one at a time; ambiguous under heavy concurrency.
    """
    result = await db.execute(
        select(Interview)
        .where(Interview.status == InterviewStatus.CALL_IN_PROGRESS)
        .options(selectinload(Interview.questions))
        .order_by(Interview.created_at.desc())
    )
    return result.scalars().first()


# Hardcoded placeholder video for every new interview until real video storage
# is wired up. Public sample MP4 that plays in any browser.
PLACEHOLDER_INTERVIEW_VIDEO_URL = (
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
)


async def update_interview_scores(
    db: AsyncSession, interview_id: str, scoring: dict, transcript: str | None = None
) -> None:
    result = await db.execute(
        select(Interview).where(Interview.id == interview_id)
    )
    interview = result.scalar_one_or_none()
    if interview is None:
        raise ValueError(f"Interview {interview_id!r} not found")

    interview.overall_score = scoring.get("overall_score")
    interview.l1_status = scoring.get("l1_status")
    interview.recommendation = scoring.get("recommendation")
    interview.status = "SCORED"
    interview.evaluation_data = scoring
    if transcript is not None:
        interview.transcript = transcript
    # Stamp the placeholder video URL on first scoring — keep any existing value otherwise.
    if not interview.video_url:
        interview.video_url = PLACEHOLDER_INTERVIEW_VIDEO_URL

    answer_map = {
        av["question"]: av for av in scoring.get("answer_validation", [])
    }

    q_result = await db.execute(
        select(InterviewQuestion).where(InterviewQuestion.interview_id == interview_id)
    )
    for q in q_result.scalars().all():
        av = answer_map.get(q.question_text)
        if av:
            q.answer_quality = av.get("answer_quality")
            q.answer_score = av.get("score")

    await db.flush()
