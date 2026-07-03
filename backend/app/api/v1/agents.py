"""Agent trigger endpoints — each returns a task_id for polling."""

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import CallStatus, InterviewStatus, TaskType
from app.config.settings import get_settings
from app.core.clients.openai_client import text_to_speech, transcribe_audio
from app.core.clients.zingaro_client import ZingaroError, place_call
from app.core.storage.local_storage import save_upload
from app.db.session import get_db_session
from app.models.candidate_main import CandidateMain
from app.repositories.candidate_repository import (
    get_main_by_ref,
    get_staging_by_ref,
    update_staging,
)
from app.repositories.interview_repository import get_interview_with_questions
from app.schemas.requests.candidate import InitiateCallRequest, ScoreInterviewRequest
from app.schemas.responses.candidate import (
    InterviewStatusResponse,
    TaskCreatedResponse,
    VoiceCallInitiatedResponse,
)
from app.services.candidate_service import create_agent_task
from app.utils.phone import to_e164
from app.workers.handlers.agent1_handler import run_agent1
from app.workers.handlers.agent2_handler import run_agent2
from app.workers.handlers.agent3_handler import run_agent3
from app.workers.handlers.agent4_handler import run_agent4
from app.workers.handlers.agent5_handler import run_agent5
from app.workers.handlers.agent_consistency_handler import run_consistency_check

router = APIRouter(tags=["Agents"])


@router.post("/agent1/parse-resume", response_model=TaskCreatedResponse)
async def parse_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    candidate_ref: str = Form(...),
    db: AsyncSession = Depends(get_db_session),
) -> TaskCreatedResponse:
    file_path, filename = await save_upload(file, "resumes")
    task_id = await create_agent_task(
        db,
        task_type=TaskType.AGENT1_RESUME_PARSE,
        reference_id=candidate_ref,
    )
    background_tasks.add_task(
        run_agent1,
        task_id=task_id,
        candidate_ref=candidate_ref,
        file_path=file_path,
        filename=filename,
        content_type=file.content_type or "application/octet-stream",
        file_size_bytes=file.size or 0,
    )
    return TaskCreatedResponse(task_id=task_id)


@router.post("/agent2/check-duplicate", response_model=TaskCreatedResponse)
async def check_duplicate(
    background_tasks: BackgroundTasks,
    candidate_ref: str,
    db: AsyncSession = Depends(get_db_session),
) -> TaskCreatedResponse:
    task_id = await create_agent_task(
        db,
        task_type=TaskType.AGENT2_DUPLICATE,
        reference_id=candidate_ref,
    )
    background_tasks.add_task(
        run_agent2,
        task_id=task_id,
        candidate_ref=candidate_ref,
    )
    return TaskCreatedResponse(task_id=task_id)


@router.post("/agent3/verify-identity", response_model=TaskCreatedResponse)
async def verify_identity(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    candidate_ref: str = Form(...),
    doc_type: str = Form(...),
    db: AsyncSession = Depends(get_db_session),
) -> TaskCreatedResponse:
    file_path, filename = await save_upload(file, "id_documents")
    task_id = await create_agent_task(
        db,
        task_type=TaskType.AGENT3_VERIFY_IDENTITY,
        reference_id=candidate_ref,
    )
    background_tasks.add_task(
        run_agent3,
        task_id=task_id,
        candidate_ref=candidate_ref,
        file_path=file_path,
        filename=filename,
        content_type=file.content_type or "image/jpeg",
        file_size_bytes=file.size or 0,
        document_type=doc_type,
    )
    return TaskCreatedResponse(task_id=task_id)


@router.post("/agent4/generate-questions", response_model=TaskCreatedResponse)
async def generate_questions(
    background_tasks: BackgroundTasks,
    candidate_ref: str,
    db: AsyncSession = Depends(get_db_session),
) -> TaskCreatedResponse:
    # Clear re-interview flag so it can only be used once
    row = await db.execute(select(CandidateMain).where(CandidateMain.candidate_ref == candidate_ref))
    candidate = row.scalar_one_or_none()
    if candidate and candidate.reinterview_allowed:
        candidate.reinterview_allowed = False
        await db.commit()

    task_id = await create_agent_task(
        db,
        task_type=TaskType.AGENT4_GENERATE_QUESTIONS,
        reference_id=candidate_ref,
    )
    background_tasks.add_task(
        run_agent4,
        task_id=task_id,
        candidate_ref=candidate_ref,
    )
    return TaskCreatedResponse(task_id=task_id)


@router.post("/agent4/transcribe-answer")
async def transcribe_answer(
    file: UploadFile,
    question_id: str = Form(...),
) -> dict:
    """Transcribe a recorded answer using Whisper. Returns transcript text immediately."""
    try:
        file_path, _ = await save_upload(file, "interview_recordings")
        transcript = await transcribe_audio(file_path)
        return {"question_id": question_id, "transcript": transcript}
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class SpeakRequest(BaseModel):
    text: str
    voice: str = "nova"


@router.post("/agent4/speak-question")
async def speak_question(body: SpeakRequest) -> Response:
    """Convert question text to spoken MP3 audio using OpenAI TTS."""
    try:
        audio_bytes = await text_to_speech(body.text, body.voice)
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Cache-Control": "no-cache"},
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


class CrossCheckRequest(BaseModel):
    candidate_ref: str
    github_url: str | None = None
    linkedin_url: str | None = None


@router.post("/agent-consistency/cross-check", response_model=TaskCreatedResponse)
async def cross_check_linkedin(
    background_tasks: BackgroundTasks,
    body: CrossCheckRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TaskCreatedResponse:
    """Save candidate-supplied URLs to staging and run a LinkedIn x resume cross-check."""
    staging = await get_staging_by_ref(db, body.candidate_ref)
    if not staging:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Persist any provided URLs (candidate-supplied values take precedence over parsed)
    updates: dict = {}
    if body.github_url:
        updates["github_url"] = body.github_url
    if body.linkedin_url:
        updates["linkedin_url"] = body.linkedin_url
    if updates:
        await update_staging(db, body.candidate_ref, **updates)
        await db.commit()

    if not (body.linkedin_url or staging.linkedin_url):
        raise HTTPException(status_code=422, detail="LinkedIn URL is required for cross-check")

    task_id = await create_agent_task(
        db,
        task_type=TaskType.AGENT_LINKEDIN_CROSSCHECK,
        reference_id=body.candidate_ref,
    )
    background_tasks.add_task(
        run_consistency_check,
        task_id=task_id,
        candidate_ref=body.candidate_ref,
    )
    return TaskCreatedResponse(task_id=task_id)


@router.post("/agent5/score-interview", response_model=TaskCreatedResponse)
async def score_interview(
    background_tasks: BackgroundTasks,
    body: ScoreInterviewRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TaskCreatedResponse:
    task_id = await create_agent_task(
        db,
        task_type=TaskType.AGENT5_SCORE_INTERVIEW,
        reference_id=body.candidate_ref,
    )
    background_tasks.add_task(
        run_agent5,
        task_id=task_id,
        candidate_ref=body.candidate_ref,
        interview_ref=body.interview_ref,
        transcript=body.transcript,
    )
    return TaskCreatedResponse(task_id=task_id)


@router.post("/voice-interview/initiate", response_model=VoiceCallInitiatedResponse)
async def initiate_voice_interview(
    body: InitiateCallRequest,
    db: AsyncSession = Depends(get_db_session),
) -> VoiceCallInitiatedResponse:
    """Place an outbound voice-interview call to the candidate.

    The questions are NOT sent here — they are injected at call time by the
    agent's pre-call webhook (POST /api/v1/voice/pre-call). We only pass the
    interview_ref in `context` so the post-call webhook can correlate the result.
    """
    settings = get_settings()
    if not settings.feature_voice_interview:
        raise HTTPException(status_code=503, detail="Voice interview is disabled")

    candidate = await get_main_by_ref(db, body.candidate_ref)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")

    interview = await get_interview_with_questions(db, body.interview_ref)
    if interview is None:
        raise HTTPException(status_code=404, detail="Interview not found")
    if str(interview.candidate_id) != str(candidate.id):
        raise HTTPException(status_code=403, detail="Interview does not belong to candidate")

    if interview.status not in (
        InterviewStatus.QUESTIONS_GENERATED,
        InterviewStatus.CALL_FAILED,
    ):
        raise HTTPException(
            status_code=409,
            detail=f"Interview is not callable in status {interview.status!r}",
        )

    phone_e164 = to_e164(candidate.phone)
    webhook_url = f"{settings.public_base_url.rstrip('/')}/api/v1/voice/post-call"

    try:
        data = await place_call(
            phone_e164,
            context={
                "interview_ref": interview.interview_ref,
                "candidate_ref": candidate.candidate_ref,
            },
            webhook_url=webhook_url,
        )
    except ZingaroError as exc:
        raise HTTPException(status_code=502, detail=f"Voice provider error: {exc}") from exc

    interview.voice_call_id = data["call_id"]
    interview.call_status = CallStatus.INITIATED
    interview.status = InterviewStatus.CALL_IN_PROGRESS

    return VoiceCallInitiatedResponse(
        interview_ref=interview.interview_ref,
        call_id=data["call_id"],
        status=InterviewStatus.CALL_IN_PROGRESS,
    )


@router.get(
    "/voice-interview/{interview_ref}/status",
    response_model=InterviewStatusResponse,
)
async def voice_interview_status(
    interview_ref: str,
    db: AsyncSession = Depends(get_db_session),
) -> InterviewStatusResponse:
    """Poll interview/call status until SCORED or CALL_FAILED.

    The SCORED outcome arrives asynchronously via the post-call webhook, so the
    frontend polls this instead of a task id.
    """
    interview = await get_interview_with_questions(db, interview_ref)
    if interview is None:
        raise HTTPException(status_code=404, detail="Interview not found")
    return InterviewStatusResponse(
        interview_ref=interview.interview_ref,
        status=interview.status,
        call_status=interview.call_status,
        overall_score=interview.overall_score,
        l1_status=interview.l1_status,
        recommendation=interview.recommendation,
        evaluation=interview.evaluation_data if interview.status == InterviewStatus.SCORED else None,
    )
