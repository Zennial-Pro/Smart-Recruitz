"""Handler for post-call voice-interview processing.

Runs after Zingaro reports a completed interview call: fetch the transcript
(which can lag the call end, so retry a few times), flatten it, then reuse the
existing Agent 5 scoring + candidate-transition logic.
"""

import asyncio

import structlog

from app.config.constants import CallStatus, InterviewStatus
from app.core.clients.zingaro_client import flatten_transcript, get_transcript
from app.db.session import async_session_factory
from app.repositories import task_repository
from app.repositories.interview_repository import get_interview_with_questions
from app.workers.handlers.agent5_handler import score_and_update

logger = structlog.get_logger(__name__)

# Transcripts can lag the call end; retry a few times before giving up.
_TRANSCRIPT_ATTEMPTS = 4
_TRANSCRIPT_BACKOFF_SECONDS = 3


async def _fetch_transcript_with_retries(call_id: str) -> dict | None:
    for attempt in range(_TRANSCRIPT_ATTEMPTS):
        data = await get_transcript(call_id)
        if data and data.get("transcript"):
            return data
        if attempt < _TRANSCRIPT_ATTEMPTS - 1:
            await asyncio.sleep(_TRANSCRIPT_BACKOFF_SECONDS * (attempt + 1))
    return None


async def run_voice_postcall(
    task_id: str,
    candidate_ref: str,
    interview_ref: str,
    call_id: str,
    transcript: str | None = None,
    meta: dict | None = None,
) -> None:
    """Score a completed voice interview.

    If `transcript` is provided (the post-call webhook already carried the
    `conversation`), score it directly. Otherwise fetch it from the transcript
    API using `call_id` (with retries, since transcripts can lag the call end).
    """
    meta = meta or {}
    async with async_session_factory() as db:
        await task_repository.mark_processing(db, task_id)
        await db.commit()

        try:
            interview = await get_interview_with_questions(db, interview_ref)
            if not interview:
                raise ValueError(f"Interview {interview_ref!r} not found")

            if not transcript:
                data = await _fetch_transcript_with_retries(call_id) if call_id else None
                if not data:
                    # Call completed but no transcript materialized — flag for manual review.
                    interview.call_status = CallStatus.COMPLETED
                    interview.status = InterviewStatus.CALL_FAILED
                    await db.commit()
                    await task_repository.mark_failed(
                        db, task_id, "transcript unavailable after retries"
                    )
                    await db.commit()
                    logger.warning(
                        "voice_postcall.no_transcript", interview_ref=interview_ref, call_id=call_id
                    )
                    return
                transcript = flatten_transcript(data.get("transcript"))
                meta.setdefault("summary", data.get("summary"))
                meta.setdefault("duration", data.get("duration"))

            interview.call_status = CallStatus.COMPLETED

            result_dict = await score_and_update(db, interview, candidate_ref, transcript)

            # The voice call recording IS the interview "video" — surface it on the
            # interview so the hiring-manager view links to the real recording instead
            # of the placeholder that scoring stamps when video_url was empty.
            # NOTE: this is a presigned S3 URL that expires (~24h); for a durable link,
            # download the file into app/core/storage and store that path instead.
            if meta.get("recording_url"):
                interview.video_url = meta["recording_url"]

            # Stash the platform's call summary/duration/recording alongside the scoring
            # blob (update_interview_scores owns evaluation_data, so merge after it runs).
            if interview.evaluation_data is not None:
                interview.evaluation_data = {
                    **interview.evaluation_data,
                    "voice_call": {
                        "call_id": call_id,
                        "summary": meta.get("summary"),
                        "duration": meta.get("duration"),
                        "recording_url": meta.get("recording_url"),
                    },
                }

            await db.commit()

            await task_repository.mark_completed(db, task_id, result_dict)
            await db.commit()
            logger.info(
                "voice_postcall.scored",
                interview_ref=interview_ref,
                call_id=call_id,
                overall_score=result_dict.get("overall_score"),
            )

        except Exception as exc:
            await db.rollback()
            async with async_session_factory() as err_db:
                await task_repository.mark_failed(err_db, task_id, str(exc))
                # Don't strand the interview at CALL_IN_PROGRESS — the candidate portal
                # polls until a terminal state, so flag it FAILED to surface a retry.
                iv = await get_interview_with_questions(err_db, interview_ref)
                if iv and iv.status != InterviewStatus.SCORED:
                    iv.status = InterviewStatus.CALL_FAILED
                    iv.call_status = CallStatus.FAILED
                await err_db.commit()
            raise
