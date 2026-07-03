"""Server-to-server webhooks for the Zingaro voice-interview platform.

These are called by Zingaro (NOT by a logged-in user), so they are mounted
without JWT auth and instead verify a shared secret / HMAC signature.

  POST /voice/pre-call   — question injection. Zingaro sends {agent_id, phone,
        country_code} just before connecting; we look up the candidate by phone
        and return {"content": "<questions the agent should ask>"}.
  POST /voice/post-call  — completion. Zingaro reports the finished call; we
        correlate it to the interview and enqueue Agent 5 scoring.
"""

import hashlib
import hmac

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import DEFAULT_QUESTION_COUNT, CallStatus, InterviewStatus, TaskType
from app.config.settings import get_settings
from app.core.clients.zingaro_client import flatten_transcript
from app.db.session import get_db_session
from app.models.candidate_main import CandidateMain
from app.models.interview import Interview
from app.repositories.candidate_repository import find_by_canonical_phone
from app.repositories.interview_repository import (
    get_active_interview_by_candidate_id,
    get_interview_by_call_id,
    get_interview_with_questions,
    get_latest_in_progress_interview,
)
from app.services.candidate_service import create_agent_task
from app.utils.phone import canonical_phone
from app.workers.handlers.voice_postcall_handler import run_voice_postcall

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/voice", tags=["Voice Webhooks"])

# Polite line spoken when we can't match the caller to an interview — never 500
# mid-dial, and never leak that no record was found in a way that breaks the call.
_FALLBACK_CONTENT = (
    "Greet the caller warmly. Explain that we could not locate their scheduled "
    "interview right now, apologize for the inconvenience, let them know our team "
    "will reach out shortly, and end the call politely."
)

# Call outcomes that mean the candidate actually went through the interview.
_COMPLETED_STATUSES = {"completed", "answered", "success", "ended", "done"}
# Outcomes where the candidate never really connected.
_NO_ANSWER_STATUSES = {"no_answer", "no-answer", "noanswer", "busy", "rejected", "cancelled", "canceled"}


def _verify(request: Request, raw_body: bytes) -> bool:
    """Verify the inbound webhook against the shared secret.

    Matches how Zingaro authenticates outgoing webhooks (configured per agent):
      - API Key  → set the header name to `X-Webhook-Secret`, value = the secret.
      - Bearer   → `Authorization: Bearer <secret>`.
    Also accepts an `X-CW-Signature` HMAC-SHA256 hex digest over the raw body, or a
    `?secret=` query param, for flexibility. Constant-time compare throughout.
    """
    settings = get_settings()
    secret = settings.zingaro_webhook_secret.get_secret_value()
    api_key = settings.zingaro_api_key.get_secret_value()
    # Accept either the dedicated webhook secret OR the call API key as the shared
    # value, so it works whichever you put in the Zingaro auth field.
    accepted = [s for s in (secret, api_key) if s]
    if not accepted:
        # Nothing configured → don't enforce (local dev only).
        return True

    def _matches(value: str | None) -> bool:
        return bool(value) and any(hmac.compare_digest(value, a) for a in accepted)

    # 1) Static shared value via a custom header (X-API-Key / X-Webhook-Secret) or query.
    provided = (
        request.headers.get("X-API-Key")
        or request.headers.get("X-Webhook-Secret")
        or request.query_params.get("secret")
    )
    if _matches(provided):
        return True

    # 2) Bearer token.
    authz = request.headers.get("Authorization", "")
    if authz.lower().startswith("bearer ") and _matches(authz.split(" ", 1)[1].strip()):
        return True

    # 3) HMAC signature over the raw body (verified against the webhook secret).
    sig = request.headers.get("X-CW-Signature") or request.headers.get("X-Webhook-Signature")
    if sig and secret:
        expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(sig, expected)

    return False


def _build_interview_content(candidate: CandidateMain, interview: Interview) -> str:
    """Build the `content` string injected into the voice agent for this call.

    Includes the role context + the numbered questions. Deliberately EXCLUDES
    expected_answer_points so the agent can't read out the answers.
    """
    role = candidate.target_role or candidate.current_title or "the applied role"
    questions = list(interview.questions or [])[:DEFAULT_QUESTION_COUNT]

    lines = [
        f"You are conducting a structured L1 screening phone interview for "
        f"{candidate.full_name}, who is applying for {role}.",
        "Greet them by name, confirm you are speaking to the right person, and "
        "explain this is a short voice screening that will be recorded and evaluated.",
        "Ask the following questions one at a time, in order. Wait for a full answer "
        "and ask a brief follow-up only if an answer is unclear, then move on. Do not "
        "reveal or hint at expected answers. Keep a professional, friendly tone.",
        "",
        "Questions:",
    ]
    for i, q in enumerate(questions, start=1):
        category = f"[{q.category}] " if q.category else ""
        lines.append(f"{i}. {category}{q.question_text}")
    lines.append("")
    lines.append("When all questions are answered, thank the candidate and end the call.")
    return "\n".join(lines)


@router.post("/pre-call")
async def pre_call_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Inject the candidate's interview questions into the call (by phone lookup)."""
    raw = await request.body()
    if not _verify(request, raw):
        logger.warning("voice.pre_call.bad_signature")
        # Return benign content rather than a hard error so a misconfigured secret
        # doesn't abort the live call; the warning is logged for ops.
        return {"content": _FALLBACK_CONTENT}

    try:
        body = await request.json()
    except Exception:
        return {"content": _FALLBACK_CONTENT}

    phone = body.get("phone") or ""
    country_code = body.get("country_code")
    canonical = canonical_phone(phone, country_code)

    candidate: CandidateMain | None = None
    interview: Interview | None = None

    # 1) Match by phone (preferred). Resolve to the candidate with an active
    #    interview; pick the newest if several share the number.
    matches: list[tuple[CandidateMain, Interview]] = []
    for cand in await find_by_canonical_phone(db, canonical):
        iv = await get_active_interview_by_candidate_id(db, cand.id)
        if iv:
            matches.append((cand, iv))
    if matches:
        if len(matches) > 1:
            logger.warning(
                "voice.pre_call.phone_collision",
                phone=phone,
                candidate_refs=[c.candidate_ref for c, _ in matches],
            )
            matches.sort(key=lambda m: m[1].created_at, reverse=True)
        candidate, interview = matches[0]

    # 2) Recency fallback — the direct-ai-call pre-call payload often carries an
    #    empty phone, so match the most recent in-progress call (set by /initiate).
    if interview is None:
        interview = await get_latest_in_progress_interview(db)
        if interview is not None:
            row = await db.execute(
                select(CandidateMain).where(CandidateMain.id == interview.candidate_id)
            )
            candidate = row.scalar_one_or_none()
            if candidate is not None:
                logger.warning(
                    "voice.pre_call.correlated_by_recency",
                    interview_ref=interview.interview_ref,
                    phone=phone,
                )

    if candidate is None or interview is None:
        logger.warning("voice.pre_call.no_match", phone=phone)
        return {"content": _FALLBACK_CONTENT}

    # Opportunistically mark in-progress (covers a manually-dialed interview that
    # never went through the initiate endpoint).
    if interview.status == InterviewStatus.QUESTIONS_GENERATED:
        interview.status = InterviewStatus.CALL_IN_PROGRESS
        interview.call_status = CallStatus.IN_PROGRESS

    content = _build_interview_content(candidate, interview)
    logger.info(
        "voice.pre_call.served",
        candidate_ref=candidate.candidate_ref,
        interview_ref=interview.interview_ref,
        question_count=len(interview.questions or []),
    )
    return {"content": content}


@router.post("/post-call")
async def post_call_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Receive call completion; correlate, then enqueue Agent 5 scoring."""
    raw = await request.body()
    if not _verify(request, raw):
        logger.warning("voice.post_call.bad_signature")
        return {"ok": False, "reason": "unauthorized"}

    try:
        body = await request.json()
    except Exception:
        return {"ok": False, "reason": "invalid_json"}

    call_id = body.get("call_id") or body.get("id") or body.get("session_id")
    call_outcome = (body.get("status") or "").strip().lower()
    context = body.get("context") or {}
    interview_ref = context.get("interview_ref")
    candidate_ref = context.get("candidate_ref")

    # Correlate, most-specific first: the interview_ref we passed on the call, then
    # the Zingaro call/session id, then the candidate's phone (the agent-level
    # post-call webhook carries only phone — no `context`/`call_id`).
    interview: Interview | None = None
    if interview_ref:
        interview = await get_interview_with_questions(db, interview_ref)
    if interview is None and call_id:
        interview = await get_interview_by_call_id(db, call_id)
    if interview is None and body.get("phone"):
        canonical = canonical_phone(body.get("phone"), body.get("country_code"))
        for cand in await find_by_canonical_phone(db, canonical):
            interview = await get_active_interview_by_candidate_id(db, cand.id)
            if interview:
                candidate_ref = candidate_ref or cand.candidate_ref
                break

    if interview is None:
        # Last resort: the direct-ai-call post-call carries no usable identifier
        # (empty phone, our metadata not echoed, session_id != placed call id), so
        # match the most recent in-progress call. Safe for serial calls.
        interview = await get_latest_in_progress_interview(db)
        if interview:
            logger.warning(
                "voice.post_call.correlated_by_recency",
                interview_ref=interview.interview_ref,
                call_id=call_id,
            )

    if interview is None:
        logger.warning("voice.post_call.no_match", call_id=call_id, interview_ref=interview_ref, phone=body.get("phone"))
        return {"ok": False, "reason": "interview_not_found"}

    # Idempotency — Zingaro may redeliver. Don't re-score a scored interview.
    if interview.status == InterviewStatus.SCORED:
        return {"ok": True, "already_scored": True}

    if not interview.voice_call_id and call_id:
        interview.voice_call_id = call_id

    # Resolve candidate_ref if it wasn't carried in the context / phone match.
    if not candidate_ref:
        row = await db.execute(
            select(CandidateMain.candidate_ref).where(CandidateMain.id == interview.candidate_id)
        )
        candidate_ref = row.scalar_one_or_none()
    if not candidate_ref:
        logger.warning("voice.post_call.no_candidate_ref", interview_ref=interview.interview_ref)
        return {"ok": False, "reason": "candidate_not_found"}

    # Failed / not-answered → candidate stays eligible, re-dial allowed. No scoring.
    if call_outcome and call_outcome not in _COMPLETED_STATUSES:
        interview.call_status = (
            CallStatus.NO_ANSWER if call_outcome in _NO_ANSWER_STATUSES else CallStatus.FAILED
        )
        interview.status = InterviewStatus.CALL_FAILED
        logger.info(
            "voice.post_call.failed",
            interview_ref=interview.interview_ref,
            outcome=call_outcome,
        )
        return {"ok": True, "outcome": call_outcome}

    # Completed → score. Prefer the transcript already in the payload (`conversation`);
    # otherwise the handler fetches it via the transcript API using call_id.
    interview.call_status = CallStatus.COMPLETED
    turns = body.get("conversation") or body.get("transcript")
    inline_transcript = flatten_transcript(turns) if turns else None
    meta = {
        "summary": body.get("summary"),
        "duration": body.get("duration_seconds") or body.get("duration"),
        "recording_url": body.get("recording_url"),
    }
    task_id = await create_agent_task(
        db,
        task_type=TaskType.AGENT5_SCORE_INTERVIEW,
        reference_id=candidate_ref,
    )
    background_tasks.add_task(
        run_voice_postcall,
        task_id=task_id,
        candidate_ref=candidate_ref,
        interview_ref=interview.interview_ref,
        call_id=interview.voice_call_id or call_id or "",
        transcript=inline_transcript,
        meta=meta,
    )
    logger.info(
        "voice.post_call.enqueued",
        interview_ref=interview.interview_ref,
        call_id=call_id,
        task_id=task_id,
        inline_transcript=bool(inline_transcript),
    )
    return {"ok": True, "task_id": task_id}
