"""CRUD operations for CandidateStaging and CandidateMain."""

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.background_task import BackgroundTask
from app.models.candidate_education import CandidateEducation
from app.models.candidate_experience import CandidateExperience
from app.models.candidate_main import CandidateMain
from app.models.candidate_skill import CandidateSkill
from app.models.candidate_staging import CandidateStaging
from app.models.skill_taxonomy import SkillTaxonomy
from app.models.uploaded_document import UploadedDocument

# ── Staging ───────────────────────────────────────────────────────────────────

async def create_staging(db: AsyncSession, data: dict) -> CandidateStaging:
    staging = CandidateStaging(**data)
    db.add(staging)
    await db.flush()
    await db.refresh(staging)
    return staging


async def get_staging_by_ref(db: AsyncSession, ref: str) -> CandidateStaging | None:
    result = await db.execute(
        select(CandidateStaging).where(CandidateStaging.candidate_ref == ref)
    )
    return result.scalar_one_or_none()


async def update_staging(db: AsyncSession, ref: str, **kwargs) -> CandidateStaging:
    staging = await get_staging_by_ref(db, ref)
    if staging is None:
        raise ValueError(f"CandidateStaging with ref {ref!r} not found")
    for key, value in kwargs.items():
        setattr(staging, key, value)
    await db.flush()
    await db.refresh(staging)
    return staging


# ── Main ──────────────────────────────────────────────────────────────────────

async def get_candidates_for_duplicate_check(
    db: AsyncSession, full_name: str, email: str, phone: str
) -> list[CandidateMain]:
    """Return candidates that might be duplicates using pg_trgm + exact email/phone."""
    result = await db.execute(
        text(
            """
            SELECT * FROM application.lms_recruit_candidates_main
            WHERE
                similarity(full_name, :name) > 0.4
                OR email = :email
                OR phone = :phone
            LIMIT 10
            """
        ),
        {"name": full_name, "email": email, "phone": phone},
    )
    rows = result.mappings().all()
    candidates: list[CandidateMain] = []
    for row in rows:
        c = CandidateMain()
        for key, value in dict(row).items():
            if hasattr(c, key):
                setattr(c, key, value)
        candidates.append(c)
    return candidates


async def create_main_from_staging(
    db: AsyncSession, staging: CandidateStaging
) -> CandidateMain:
    # Recompute total experience from individual experience entries (more reliable
    # than the LLM-provided aggregate which can drift from the per-role durations).
    experiences = staging.experience or []
    summed_months = sum((e.get("duration_months") or 0) for e in experiences)
    summed_years = round(summed_months / 12, 1) if summed_months else 0.0
    total_years = summed_years if summed_years > 0 else (staging.total_experience_years or 0.0)

    main = CandidateMain(
        candidate_ref=staging.candidate_ref,
        full_name=staging.full_name,
        email=staging.email,
        phone=staging.phone,
        current_title=staging.current_title,
        total_experience_years=total_years,
        primary_domain=staging.primary_domain,
        target_role=staging.target_role,
        current_ctc=staging.current_ctc,
        expected_ctc=staging.expected_ctc,
        notice_period=staging.notice_period,
        working_status=staging.working_status,
        location=staging.location,
        preferred_location=staging.preferred_location,
        github_url=staging.github_url,
        linkedin_url=staging.linkedin_url,
        linkedin_cross_check=staging.linkedin_cross_check,
        resume_overall_score=staging.resume_overall_score,
        resume_analysis=staging.resume_analysis,
        status="VERIFIED",
        verification_status="PENDING",
        raw_profile_data=staging.raw_resume_data,
    )
    db.add(main)
    await db.flush()
    await db.refresh(main)
    return main


async def get_main_by_ref(db: AsyncSession, ref: str) -> CandidateMain | None:
    result = await db.execute(
        select(CandidateMain).where(CandidateMain.candidate_ref == ref)
    )
    return result.scalar_one_or_none()


async def find_by_canonical_phone(db: AsyncSession, canonical: str) -> list[CandidateMain]:
    """Return candidates whose phone matches a canonical (digits-only) subscriber number.

    The pre-call webhook only hands us the phone number, and stored phones are
    free-form, so we strip non-digits in SQL and match on the trailing subscriber
    digits (`canonical` is the 10-digit form from `canonical_phone`). Returns a
    list so callers can detect / log collisions.
    """
    if not canonical:
        return []
    stripped = func.regexp_replace(CandidateMain.phone, r"[^0-9]", "", "g")
    result = await db.execute(
        select(CandidateMain).where(stripped.like(f"%{canonical}"))
    )
    return list(result.scalars().all())


async def populate_relational_from_staging(
    db: AsyncSession, main_id: str, staging: CandidateStaging
) -> None:
    """Insert candidate_experiences, candidate_educations, and candidate_skills rows from staging JSONB."""
    import uuid as _uuid
    mid = _uuid.UUID(main_id)

    for exp in (staging.experience or []):
        db.add(CandidateExperience(
            candidate_id=mid,
            company=exp.get("company", ""),
            title=exp.get("title", ""),
            start_date=exp.get("start_date") or None,
            end_date=exp.get("end_date") or None,
            duration_months=exp.get("duration_months"),
            domain=exp.get("domain") or None,
            is_current=exp.get("is_current", False),
            company_type=(exp.get("company_type") or "OTHER").upper(),
            responsibilities=exp.get("responsibilities"),
        ))

    for edu in (staging.education or []):
        db.add(CandidateEducation(
            candidate_id=mid,
            institution=edu.get("institution", ""),
            degree=edu.get("degree", ""),
            field=edu.get("field") or None,
            graduation_year=edu.get("graduation_year"),
            start_date=edu.get("start_date") or None,
            end_date=edu.get("end_date") or None,
        ))

    # Skills — get-or-create taxonomy entries, then link via candidate_skills
    for skill in (staging.skills_normalized or []):
        name = (skill.get("standard_name") or "").strip()
        if not name:
            continue
        category = skill.get("category") or "GENERAL"

        # Look up existing taxonomy entry (case-insensitive)
        existing = await db.execute(
            select(SkillTaxonomy).where(func.lower(SkillTaxonomy.standard_name) == name.lower())
        )
        taxonomy = existing.scalar_one_or_none()
        if taxonomy is None:
            taxonomy = SkillTaxonomy(standard_name=name, category=category)
            db.add(taxonomy)
            await db.flush()

        db.add(CandidateSkill(
            candidate_id=mid,
            skill_id=taxonomy.id,
            proficiency=skill.get("proficiency") or "INTERMEDIATE",
            years_experience=skill.get("years_experience"),
            evidence=skill.get("evidence"),
            is_implied=bool(skill.get("is_implied", False)),
            confidence=skill.get("confidence"),
        ))

    await db.flush()


async def update_main(db: AsyncSession, ref: str, **kwargs) -> CandidateMain:
    main = await get_main_by_ref(db, ref)
    if main is None:
        raise ValueError(f"CandidateMain with ref {ref!r} not found")
    for key, value in kwargs.items():
        setattr(main, key, value)
    await db.flush()
    await db.refresh(main)
    return main


async def delete_candidate_cascade(db: AsyncSession, ref: str) -> dict | None:
    """Hard-delete a candidate and ALL of their data.

    Deleting the ``candidates_main`` row DB-cascades educations, experiences,
    skills, verifications, interviews and interview_questions (FK ON DELETE
    CASCADE). The records that are NOT FK-linked to main are removed explicitly:
    the staging row (keyed by ``candidate_ref``), uploaded documents (keyed by
    ``uploaded_by_ref``) and the candidate's background-task rows.

    Uses Core DELETE statements so Postgres performs the cascade directly (no ORM
    relationship side effects). Returns ``{"full_name", "storage_paths"}`` for
    post-commit on-disk file cleanup, or ``None`` if no such candidate exists.
    """
    main = (
        await db.execute(
            select(CandidateMain.id, CandidateMain.full_name).where(
                CandidateMain.candidate_ref == ref
            )
        )
    ).first()
    staging_id = await db.scalar(
        select(CandidateStaging.id).where(CandidateStaging.candidate_ref == ref)
    )
    if main is None and staging_id is None:
        return None

    # Capture document paths before the rows go away, for best-effort disk cleanup.
    doc_rows = await db.execute(
        select(UploadedDocument.storage_path).where(UploadedDocument.uploaded_by_ref == ref)
    )
    storage_paths = [r[0] for r in doc_rows.fetchall()]

    if main is not None:
        await db.execute(delete(CandidateMain).where(CandidateMain.id == main.id))
    await db.execute(delete(CandidateStaging).where(CandidateStaging.candidate_ref == ref))
    await db.execute(delete(UploadedDocument).where(UploadedDocument.uploaded_by_ref == ref))
    await db.execute(delete(BackgroundTask).where(BackgroundTask.reference_id == ref))

    return {"full_name": (main.full_name if main else ref), "storage_paths": storage_paths}
