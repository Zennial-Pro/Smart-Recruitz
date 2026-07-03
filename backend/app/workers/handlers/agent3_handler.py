"""ARQ handler for Agent 3: ID Verifier."""

from difflib import SequenceMatcher

from app.agents.agent3_id_verifier import verify_identity
from app.db.session import async_session_factory
from app.repositories import task_repository
from app.repositories.candidate_repository import (
    create_main_from_staging,
    get_main_by_ref,
    get_staging_by_ref,
    populate_relational_from_staging,
    update_main,
)
from app.repositories.document_repository import create_document
from app.repositories.verification_repository import (
    create_verification,
    get_verified_doc_types,
    update_verification,
)


# Mandatory identity documents — candidate must verify ALL of these before
# we mark verification_status=VERIFIED on candidates_main.
MANDATORY_ID_DOC_TYPES = {"AADHAAR_CARD", "PAN_CARD"}


import re


def _norm(name: str | None) -> str:
    """Normalize a name: lowercase, strip, collapse whitespace, drop punctuation."""
    if not name:
        return ""
    # Remove dots/commas (initials like "K.A. Reddy" → "ka reddy")
    cleaned = re.sub(r"[.,]", " ", name.lower())
    return " ".join(cleaned.strip().split())


def _tokens(name: str | None) -> set[str]:
    """Split a name into a set of word tokens (ignoring single-letter initials)."""
    n = _norm(name)
    if not n:
        return set()
    return {t for t in n.split() if len(t) > 1}


def _similarity(a: str | None, b: str | None) -> float:
    """Return 0..1 similarity between two names. Handles reversed order, middle-name
    omission, and initials by combining sequence match + token overlap.
    """
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return 0.0

    # 1. Direct sequence match
    direct = SequenceMatcher(None, na, nb).ratio()

    # 2. Reversed sequence match — handles "Vamshi Marepu" vs "Marepu Vamshi"
    nb_reversed = " ".join(reversed(nb.split()))
    reversed_score = SequenceMatcher(None, na, nb_reversed).ratio()

    # 3. Token overlap (Jaccard) — order-independent, handles missing/extra middle names
    ta, tb = _tokens(a), _tokens(b)
    if ta and tb:
        intersection = len(ta & tb)
        smaller = min(len(ta), len(tb))
        token_score = intersection / smaller if smaller else 0.0
    else:
        token_score = 0.0

    return max(direct, reversed_score, token_score)


NAME_MATCH_THRESHOLD = 0.75


async def run_agent3(
    task_id: str,
    candidate_ref: str,
    file_path: str,
    filename: str,
    content_type: str,
    file_size_bytes: int,
    document_type: str,
) -> None:
    async with async_session_factory() as db:
        await task_repository.mark_processing(db, task_id)
        await db.commit()

        try:
            # Staging is the original source of truth from registration. After the
            # first successful ID upload the candidate is promoted to candidates_main;
            # for the second/third ID upload (PAN, optional Passport) we may not need
            # staging at all — read it if present, otherwise fall back to main.
            staging = await get_staging_by_ref(db, candidate_ref)
            main = await get_main_by_ref(db, candidate_ref)

            if not staging and not main:
                raise ValueError(
                    f"Candidate {candidate_ref!r} not found in staging or main. "
                    "The candidate's local session may be stale (e.g. database was reset). "
                    "Ask them to re-register."
                )

            # Save ID document
            doc = await create_document(
                db,
                filename=filename,
                storage_path=file_path,
                content_type=content_type,
                file_size_bytes=file_size_bytes,
                document_category="ID_DOCUMENT",
                uploaded_by_ref=candidate_ref,
            )
            await db.commit()

            # Ensure CandidateMain exists (upsert from staging on first ID upload)
            if main is None:
                # staging is non-None here per the guard above
                main = await create_main_from_staging(db, staging)
                await populate_relational_from_staging(db, str(main.id), staging)
                await db.commit()

            # Create pending verification record
            verification = await create_verification(
                db,
                candidate_id=str(main.id),
                doc_type=document_type,
                document_id=str(doc.id),
            )
            await db.commit()

            # Prefer staging (registration data) but fall back to main when staging
            # has been wiped (e.g. dev reset, or a slow follow-on upload).
            claimed_name = (staging.full_name if staging else None) or main.full_name or ""

            # Run agent
            result = await verify_identity(
                file_path=file_path,
                content_type=content_type,
                document_type=document_type,
                claimed_name=claimed_name,
            )
            result_dict = result.model_dump()

            # ── 3-way name cross-check ─────────────────────────────────────────
            # Compare: entered name ↔ resume name ↔ ID extracted name
            entered_name = claimed_name
            raw_resume = (staging.raw_resume_data if staging else None) or main.raw_profile_data or {}
            resume_name = raw_resume.get("full_name") or ""
            id_name = (result.extracted_data or {}).get("full_name") or ""

            sim_id_vs_entered = _similarity(id_name, entered_name)
            sim_id_vs_resume = _similarity(id_name, resume_name) if resume_name else None
            sim_resume_vs_entered = _similarity(resume_name, entered_name) if resume_name else None

            cross_check_flags: list[str] = []
            if sim_id_vs_entered < NAME_MATCH_THRESHOLD:
                cross_check_flags.append("id_vs_entered_name_mismatch")
            if sim_id_vs_resume is not None and sim_id_vs_resume < NAME_MATCH_THRESHOLD:
                cross_check_flags.append("id_vs_resume_name_mismatch")
            if sim_resume_vs_entered is not None and sim_resume_vs_entered < NAME_MATCH_THRESHOLD:
                cross_check_flags.append("resume_vs_entered_name_mismatch")

            # Override status to FAILED if any cross-check fails
            final_status = result.status
            final_flags = list(result.flags) + cross_check_flags
            if cross_check_flags and final_status == "VERIFIED":
                final_status = "FAILED"

            data_match_results = dict(result.data_match_results or {})
            data_match_results.update({
                "id_vs_entered_name": round(sim_id_vs_entered, 3),
                "id_vs_resume_name": round(sim_id_vs_resume, 3) if sim_id_vs_resume is not None else None,
                "resume_vs_entered_name": round(sim_resume_vs_entered, 3) if sim_resume_vs_entered is not None else None,
                "names": {
                    "entered": entered_name,
                    "resume": resume_name,
                    "id": id_name,
                },
            })

            # Mutate result_dict for downstream consumers (frontend reads from task.result)
            result_dict["status"] = final_status
            result_dict["flags"] = final_flags
            result_dict["data_match_results"] = data_match_results

            # Update verification record
            await update_verification(
                db,
                str(verification.id),
                status=final_status,
                confidence_score=result.confidence_score,
                extracted_data=result.extracted_data,
                data_match_results=data_match_results,
                flags={"flags": final_flags},
            )
            await db.commit()

            # Mark candidates_main verified only when ALL mandatory ID docs are done.
            # A single failed verification short-circuits to FAILED.
            if final_status == "VERIFIED":
                verified_types = await get_verified_doc_types(db, str(main.id))
                all_mandatory_done = MANDATORY_ID_DOC_TYPES.issubset(verified_types)
                if all_mandatory_done:
                    await update_main(
                        db,
                        candidate_ref,
                        verification_status="VERIFIED",
                        status="IDENTITY_VERIFIED",
                    )
                # else: leave verification_status as PENDING until the other doc lands
            else:
                await update_main(
                    db,
                    candidate_ref,
                    verification_status="FAILED",
                    status="IDENTITY_FAILED",
                )
            await db.commit()

            # Surface progress so the frontend can decide what to ask next
            verified_after = await get_verified_doc_types(db, str(main.id))
            result_dict["verified_doc_types"] = sorted(verified_after)
            result_dict["all_mandatory_verified"] = MANDATORY_ID_DOC_TYPES.issubset(verified_after)
            result_dict["mandatory_doc_types"] = sorted(MANDATORY_ID_DOC_TYPES)

            await task_repository.mark_completed(db, task_id, result_dict)
            await db.commit()

        except Exception as exc:
            await db.rollback()
            async with async_session_factory() as err_db:
                await task_repository.mark_failed(err_db, task_id, str(exc))
                await err_db.commit()
            raise
