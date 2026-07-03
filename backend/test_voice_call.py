"""One-shot manual test for the Zingaro voice interview.

Seeds a throwaway candidate + interview (with questions) for a given phone number,
then places a real outbound call via Zingaro. Your phone rings; the running backend
serves the questions (pre-call webhook) and scores the call (post-call webhook).

Run on the machine that has network + the backend running:

    cd backend
    .venv/bin/python test_voice_call.py +919876543210      # the phone to call (yours)

Watch the `make dev` logs for:  voice.pre_call.served  →  voice.post_call.enqueued
Delete this file when you're done testing.
"""

import asyncio
import sys
import uuid

from sqlalchemy import text

from app.config.settings import get_settings
from app.core.clients.zingaro_client import place_call
from app.db.session import async_session_factory, engine
from app.repositories.candidate_repository import (
    delete_candidate_cascade,
    find_by_canonical_phone,
)
from app.utils.phone import canonical_phone, to_e164

QUESTIONS = [
    ("Q-001", "EXPERIENCE_VERIFICATION", "Briefly walk me through your most recent role and what you owned."),
    ("Q-002", "TECHNICAL", "Explain the difference between a process and a thread."),
    ("Q-003", "BEHAVIORAL", "Tell me about a difficult bug you fixed and how you approached it."),
]


async def main(phone: str) -> None:
    settings = get_settings()
    ref = f"SR-VOICETEST-{uuid.uuid4().hex[:6].upper()}"
    email = f"voicetest.{uuid.uuid4().hex[:8]}@example.com"
    cid = str(uuid.uuid4())
    iid = str(uuid.uuid4())

    async with async_session_factory() as db:
        # Clean up any prior test candidate that shares this phone (phone is unique).
        for cand in await find_by_canonical_phone(db, canonical_phone(phone)):
            await delete_candidate_cascade(db, cand.candidate_ref)
        await db.commit()

        # Seed a verified candidate with an interview ready to be called.
        await db.execute(text(
            "insert into application.lms_recruit_candidates_main "
            "(id, candidate_ref, status, full_name, email, phone, target_role, "
            " current_title, verification_status, reinterview_allowed) "
            "values (:id,:r,'INTERVIEW_READY','Voice Test Candidate',:e,:p,"
            "'Backend Engineer','Software Engineer','VERIFIED',false)"
        ), {"id": cid, "r": ref, "e": email, "p": phone})
        await db.execute(text(
            "insert into application.lms_recruit_interviews "
            "(id, interview_ref, candidate_id, interview_type, status) "
            "values (:id,:ir,:c,'L1_SCREENING','QUESTIONS_GENERATED')"
        ), {"id": iid, "ir": f"INT-{uuid.uuid4().hex[:8].upper()}", "c": cid})
        for qref, cat, qtext in QUESTIONS:
            await db.execute(text(
                "insert into application.lms_recruit_interview_questions "
                "(id, interview_id, question_ref, category, question_text, difficulty) "
                "values (:id,:i,:qr,:cat,:q,'MID')"
            ), {"id": str(uuid.uuid4()), "i": iid, "qr": qref, "cat": cat, "q": qtext})
        await db.commit()

        interview_ref = (await db.execute(
            text("select interview_ref from application.lms_recruit_interviews where id=:i"),
            {"i": iid},
        )).scalar_one()

    phone_e164 = to_e164(phone)
    webhook_url = f"{settings.public_base_url.rstrip('/')}/api/v1/voice/post-call"
    print(f"Seeded candidate {ref} / interview {interview_ref}")
    print(f"Placing call to {phone_e164} via agent {settings.zingaro_agent_id} ...")
    print(f"post-call webhook -> {webhook_url}")

    data = await place_call(
        phone_e164,
        context={"interview_ref": interview_ref, "candidate_ref": ref},
        webhook_url=webhook_url,
    )
    # Mirror what the real /initiate endpoint does, so the post-call recency match works.
    async with async_session_factory() as db:
        await db.execute(text(
            "update application.lms_recruit_interviews set status='CALL_IN_PROGRESS', "
            "call_status='INITIATED', voice_call_id=:cid where id=:i"
        ), {"cid": data.get("call_id"), "i": iid})
        await db.commit()
    print("\n✅ Call placed. call_id =", data.get("call_id"), "status =", data.get("status"))
    print("Answer your phone. Watch the backend logs for:")
    print("   voice.pre_call.served   (questions injected)")
    print("   voice.post_call.enqueued (scoring started)")
    print(f"\nThen check the result:  GET /api/v1/voice-interview/{interview_ref}/status")

    await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python test_voice_call.py <phone, e.g. +919876543210>")
        raise SystemExit(1)
    asyncio.run(main(sys.argv[1]))
