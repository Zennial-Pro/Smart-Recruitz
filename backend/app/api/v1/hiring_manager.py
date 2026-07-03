"""Hiring Manager API — candidate search, filters, dashboard stats."""

import contextlib
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.jd_extractor import extract_jd
from app.core.security.integration_auth import (
    IntegrationPrincipal,
    require_hiring_manager,
)
from app.db.session import get_db_session
from app.models.candidate_main import CandidateMain
from app.models.candidate_skill import CandidateSkill
from app.models.interview import Interview
from app.models.skill_taxonomy import SkillTaxonomy
from app.repositories.candidate_repository import delete_candidate_cascade
from app.services.lms_webhook import notify_lms_decision
from app.utils.document_text import extract_text

router = APIRouter(prefix="/hiring-manager", tags=["hiring-manager"])


# ── Dashboard ──────────────────────────────────────────────────────────────────

@router.get("/dashboard")
async def get_dashboard(db: AsyncSession = Depends(get_db_session)):
    total = await db.scalar(select(func.count()).select_from(CandidateMain))
    verified = await db.scalar(
        select(func.count()).select_from(CandidateMain)
        .where(CandidateMain.verification_status == "VERIFIED")
    )
    avg_score = await db.scalar(
        select(func.avg(Interview.overall_score))
        .where(Interview.overall_score.isnot(None))
    )
    passed = await db.scalar(
        select(func.count()).select_from(Interview)
        .where(Interview.l1_status == "PASSED")
    )

    # Domain breakdown
    domain_rows = await db.execute(
        select(CandidateMain.primary_domain, func.count().label("count"))
        .where(CandidateMain.primary_domain.isnot(None))
        .group_by(CandidateMain.primary_domain)
        .order_by(func.count().desc())
        .limit(8)
    )
    domains = [{"domain": r[0], "count": r[1]} for r in domain_rows.fetchall()]

    # Recent 5 candidates
    recent_rows = await db.execute(
        select(CandidateMain)
        .order_by(CandidateMain.created_at.desc())
        .limit(5)
    )
    recent = [_candidate_summary(c) for c in recent_rows.scalars().all()]

    return {
        "total_candidates": total or 0,
        "verified_candidates": verified or 0,
        "avg_interview_score": round(avg_score or 0, 1),
        "l1_passed": passed or 0,
        "domain_breakdown": domains,
        "recent_candidates": recent,
    }


# ── Candidate List + Search ────────────────────────────────────────────────────

@router.get("/candidates")
async def list_candidates(
    db: AsyncSession = Depends(get_db_session),
    domain: str | None = Query(None),
    min_score: float | None = Query(None),
    max_score: float | None = Query(None),
    min_experience: float | None = Query(None),
    min_resume_score: float | None = Query(None, description="Filter by resume_overall_score >="),
    min_product_years: float | None = Query(None, description="Filter by product_experience_years >= (reads resume_analysis.analytics)"),
    company_type: str | None = Query(None, description="Filter by dominant_company_type: PRODUCT | SERVICE | GCC | STARTUP"),
    l1_status: str | None = Query(None),
    skills: str | None = Query(None, description="Comma-separated skill names"),
    search: str | None = Query(None, description="Name or title search"),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
):
    query = (
        select(CandidateMain)
        .options(
            selectinload(CandidateMain.skills).selectinload(CandidateSkill.skill),
            selectinload(CandidateMain.experiences),
            selectinload(CandidateMain.interviews),
        )
    )

    if domain:
        query = query.where(CandidateMain.primary_domain.ilike(f"%{domain}%"))
    if min_experience is not None:
        query = query.where(CandidateMain.total_experience_years >= min_experience)
    if min_resume_score is not None:
        query = query.where(CandidateMain.resume_overall_score >= min_resume_score)
    if min_product_years is not None:
        # JSONB path: resume_analysis -> 'analytics' -> 'product_experience_years'
        query = query.where(
            CandidateMain.resume_analysis["analytics"]["product_experience_years"].as_float() >= min_product_years
        )
    if company_type:
        query = query.where(
            CandidateMain.resume_analysis["analytics"]["dominant_company_type"].as_string() == company_type.upper()
        )
    if search:
        query = query.where(
            CandidateMain.full_name.ilike(f"%{search}%") |
            CandidateMain.current_title.ilike(f"%{search}%")
        )

    # Score filters — join interviews
    if min_score is not None or max_score is not None or l1_status:
        query = query.join(
            Interview,
            Interview.candidate_id == CandidateMain.id,
            isouter=True,
        )
        if min_score is not None:
            query = query.where(Interview.overall_score >= min_score)
        if max_score is not None:
            query = query.where(Interview.overall_score <= max_score)
        if l1_status:
            query = query.where(Interview.l1_status == l1_status.upper())

    # Skills filter — candidate must have ALL listed skills
    if skills:
        skill_list = [s.strip().lower() for s in skills.split(",") if s.strip()]
        for skill_name in skill_list:
            subq = (
                select(CandidateSkill.candidate_id)
                .join(SkillTaxonomy, SkillTaxonomy.id == CandidateSkill.skill_id)
                .where(SkillTaxonomy.standard_name.ilike(f"%{skill_name}%"))
            )
            query = query.where(CandidateMain.id.in_(subq))

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)

    query = query.order_by(CandidateMain.created_at.desc()).limit(limit).offset(offset)
    rows = await db.execute(query)
    candidates = rows.scalars().unique().all()

    return {
        "total": total or 0,
        "candidates": [_candidate_card(c) for c in candidates],
    }


@router.post("/search")
async def search_candidates(
    body: dict,
    db: AsyncSession = Depends(get_db_session),
):
    """Search by JD text + skill lists. Returns ranked candidates.

    Body shape:
        {
          "mandatory_skills": ["Python", "FastAPI"],   # HARD FILTER — candidate must have ALL
          "preferred_skills": ["Kubernetes", "GCP"],   # nice-to-have — boosts ranking
          "skills": [...],                             # legacy alias for mandatory_skills
          "required_skills": [...],                    # legacy alias for mandatory_skills (back-compat)
          "jd_text": "..."                             # if no skills provided, auto-extracted into mandatory
        }

    Scoring weights:
        mandatory: 70%   (all-or-nothing gate — passing contributes the full 70)
        preferred: 30%   (% of preferred skills matched × 30)
    Score is renormalized to 0-100 when only one bucket is used.
    """
    # Accept legacy `skills` / `required_skills` as aliases for `mandatory_skills` (strictest fallback)
    mandatory_input: list[str] = (
        body.get("mandatory_skills")
        or body.get("required_skills")
        or body.get("skills")
        or []
    )
    preferred_input: list[str] = body.get("preferred_skills") or []
    jd_text: str = body.get("jd_text", "")
    # Optional location filter — matches the candidate's current OR preferred location.
    location_q: str = (body.get("location") or "").strip().lower()

    # Auto-extract from JD text into MANDATORY when no skills supplied (raw text fallback only)
    if jd_text and not mandatory_input and not preferred_input:
        taxonomy_rows = await db.execute(select(SkillTaxonomy.standard_name))
        all_skills = [r[0] for r in taxonomy_rows.fetchall()]
        jd_lower = jd_text.lower()
        mandatory_input = [s for s in all_skills if s.lower() in jd_lower][:15]

    # Nothing to search by (no skills AND no location) → empty result.
    if not mandatory_input and not preferred_input and not location_q:
        return {
            "mandatory_matched": [],
            "preferred_matched": [],
            "skills_matched": [],  # legacy
            "candidates": [],
        }

    mand_lower = [s.lower() for s in mandatory_input]
    pref_lower = [s.lower() for s in preferred_input]

    rows = await db.execute(
        select(CandidateMain)
        .options(
            selectinload(CandidateMain.skills).selectinload(CandidateSkill.skill),
            selectinload(CandidateMain.experiences),
            selectinload(CandidateMain.interviews),
        )
    )
    all_candidates = rows.scalars().unique().all()

    # Bucket weights (only buckets actually in use contribute to renormalization)
    W_MANDATORY, W_PREFERRED = 0.70, 0.30
    weight_total = (
        (W_MANDATORY if mand_lower else 0)
        + (W_PREFERRED if pref_lower else 0)
    )

    results = []
    for c in all_candidates:
        # HARD FILTER: location (matches current OR preferred, case-insensitive substring)
        if location_q:
            cand_loc = (c.location or "").lower()
            pref_loc = (c.preferred_location or "").lower()
            if location_q not in cand_loc and location_q not in pref_loc:
                continue

        candidate_skills = {cs.skill.standard_name.lower() for cs in c.skills if cs.skill}

        # Substring match: "react" matches "react.js"
        matched_mand = [s for s in mand_lower if any(s in cs for cs in candidate_skills)]
        matched_pref = [s for s in pref_lower if any(s in cs for cs in candidate_skills)]

        # HARD FILTER: candidate must have ALL mandatory skills
        if mand_lower and len(matched_mand) < len(mand_lower):
            continue

        # Weighted score per bucket, normalized to 0-100 over only the buckets in use
        raw = 0.0
        if mand_lower:
            raw += W_MANDATORY  # filter already passed
        if pref_lower:
            raw += W_PREFERRED * (len(matched_pref) / len(pref_lower))
        match_score = round((raw / weight_total) * 100) if weight_total else 0
        # Location-only search (no skills): candidate already passed the location
        # filter, so surface them at full score.
        if weight_total == 0 and location_q:
            match_score = 100

        # When there's no skill filter, no skill match, and no location filter, skip
        if not mand_lower and not matched_pref and not location_q:
            continue

        # Map matched lowercase back to original-case input for nice display
        matched_mand_orig = [s for s in mandatory_input if s.lower() in matched_mand]
        matched_pref_orig = [s for s in preferred_input if s.lower() in matched_pref]

        card = _candidate_card(c)
        card["match_score"] = match_score
        card["matched_mandatory"] = matched_mand_orig
        card["matched_preferred"] = matched_pref_orig
        # Legacy alias used by older callers/UI
        card["matched_skills"] = matched_mand_orig + matched_pref_orig
        results.append(card)

    results.sort(key=lambda x: x["match_score"], reverse=True)

    return {
        "mandatory_matched": mandatory_input,
        "preferred_matched": preferred_input,
        "skills_matched": mandatory_input + preferred_input,  # legacy
        "location": body.get("location") or "",
        "candidates": results[:50],
    }


# ── JD Extraction ─────────────────────────────────────────────────────────────

# Larger than resumes — JDs are usually shorter but can include policy text + benefits.
MAX_JD_FILE_BYTES = 5 * 1024 * 1024


@router.post("/extract-jd")
async def extract_jd_endpoint(
    file: UploadFile | None = File(None),
    jd_text: str | None = Form(None),
):
    """Parse an uploaded JD (PDF / DOCX / TXT) OR raw text and return structured criteria.

    Either `file` or `jd_text` (form-encoded) must be provided.
    Response shape matches `JDExtractionOutput` plus an `extracted_text` preview.
    """
    text: str = ""

    if file is not None:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=422, detail="Uploaded file is empty")
        if len(contents) > MAX_JD_FILE_BYTES:
            raise HTTPException(status_code=413, detail="File too large (max 5MB)")
        try:
            text = extract_text(contents, file.content_type, file.filename)
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Could not parse file: {exc}",
            ) from exc
    elif jd_text is not None:
        text = jd_text.strip()

    if not text:
        raise HTTPException(status_code=422, detail="No JD text could be extracted")

    result = await extract_jd(text)
    return {
        **result.model_dump(),
        "extracted_text_preview": text[:1500],
        "extracted_text_length": len(text),
    }


# ── Candidate Detail ───────────────────────────────────────────────────────────

@router.get("/candidates/{candidate_ref}")
async def get_candidate(
    candidate_ref: str,
    db: AsyncSession = Depends(get_db_session),
):
    row = await db.execute(
        select(CandidateMain)
        .where(CandidateMain.candidate_ref == candidate_ref)
        .options(
            selectinload(CandidateMain.skills).selectinload(CandidateSkill.skill),
            selectinload(CandidateMain.experiences),
            selectinload(CandidateMain.educations),
            selectinload(CandidateMain.interviews).selectinload(Interview.questions),
        )
    )
    c = row.scalar_one_or_none()
    if not c:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Candidate not found")

    latest_interview = max(
        (i for i in c.interviews if i.overall_score is not None),
        key=lambda i: i.created_at,
        default=None,
    ) if c.interviews else None

    return {
        **_candidate_card(c),
        "email": c.email,
        "phone": c.phone,
        "target_role": c.target_role,
        "location": c.location,
        "resume_analysis": c.resume_analysis,
        "linkedin_cross_check": c.linkedin_cross_check,
        "talent_pool_entry_date": c.talent_pool_entry_date.isoformat() if c.talent_pool_entry_date else None,
        "skills": [
            {
                "name": cs.skill.standard_name if cs.skill else "",
                "proficiency": cs.proficiency,
                "years": cs.years_experience,
                "category": cs.skill.category if cs.skill else "",
            }
            for cs in c.skills if cs.skill
        ],
        "experience": [
            {
                "company": e.company,
                "title": e.title,
                "start_date": e.start_date,
                "end_date": e.end_date,
                "duration_months": e.duration_months,
                "is_current": e.is_current,
                "domain": e.domain,
                "company_type": e.company_type,
            }
            for e in sorted(c.experiences, key=lambda x: x.is_current, reverse=True)
        ],
        "education": [
            {
                "institution": ed.institution,
                "degree": ed.degree,
                "field": ed.field,
                "graduation_year": ed.graduation_year,
            }
            for ed in c.educations
        ],
        "interview": {
            "interview_ref": latest_interview.interview_ref,
            "status": latest_interview.status,
            "overall_score": latest_interview.overall_score,
            "l1_status": latest_interview.l1_status,
            "recommendation": latest_interview.recommendation,
            "video_url": latest_interview.video_url,
            "transcript": latest_interview.transcript,
            "evaluation": latest_interview.evaluation_data,
            "questions": _enrich_questions_with_answers(latest_interview),
        } if latest_interview else None,
        "all_interviews": [
            {
                "interview_ref": i.interview_ref,
                "overall_score": i.overall_score,
                "l1_status": i.l1_status,
                "created_at": i.created_at.isoformat(),
            }
            for i in sorted(c.interviews, key=lambda x: x.created_at, reverse=True)
        ],
    }


# ── Re-interview ──────────────────────────────────────────────────────────────

@router.post("/candidates/{candidate_ref}/allow-reinterview")
async def allow_reinterview(
    candidate_ref: str,
    db: AsyncSession = Depends(get_db_session),
):
    row = await db.execute(
        select(CandidateMain).where(CandidateMain.candidate_ref == candidate_ref)
    )
    c = row.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    c.reinterview_allowed = True
    await db.commit()
    return {"success": True, "message": f"Re-interview enabled for {c.full_name}"}


# ── Delete candidate ────────────────────────────────────────────────────────────

@router.delete("/candidates/{candidate_ref}")
async def delete_candidate(
    candidate_ref: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Permanently delete a candidate and ALL related data (staging, profile,
    skills, experience, education, verifications, interviews + questions, uploaded
    documents and background tasks). Destructive and irreversible.
    """
    result = await delete_candidate_cascade(db, candidate_ref)
    if result is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    await db.commit()

    # Best-effort: remove the candidate's uploaded files from disk after the DB delete.
    for path in result["storage_paths"]:
        with contextlib.suppress(OSError):
            Path(path).unlink(missing_ok=True)

    return {
        "success": True,
        "candidate_ref": candidate_ref,
        "message": f"Deleted {result['full_name']} and all associated data",
    }


# ── LMS approval decisions ───────────────────────────────────────────────────────

async def _record_decision(candidate_ref: str, decision: str, db: AsyncSession) -> dict:
    """Persist an approve/reject decision and notify the LMS via webhook."""
    row = await db.execute(
        select(CandidateMain)
        .where(CandidateMain.candidate_ref == candidate_ref)
        .options(selectinload(CandidateMain.interviews))
    )
    c = row.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")

    c.status = "LMS_APPROVED" if decision == "approved" else "LMS_REJECTED"
    await db.commit()

    latest = max(
        (i for i in c.interviews if i.overall_score is not None),
        key=lambda i: i.created_at,
        default=None,
    ) if c.interviews else None
    scored_result = {
        "overall_score": latest.overall_score if latest else None,
        "l1_status": latest.l1_status if latest else None,
        "recommendation": latest.recommendation if latest else None,
    }

    delivered = await notify_lms_decision(candidate_ref, decision, scored_result)
    return {
        "success": True,
        "candidate_ref": candidate_ref,
        "decision": decision,
        "webhook_delivered": delivered,
    }


@router.post("/candidates/{candidate_ref}/approve")
async def approve_candidate(
    candidate_ref: str,
    db: AsyncSession = Depends(get_db_session),
    _: IntegrationPrincipal = Depends(require_hiring_manager),
):
    return await _record_decision(candidate_ref, "approved", db)


@router.post("/candidates/{candidate_ref}/reject")
async def reject_candidate(
    candidate_ref: str,
    db: AsyncSession = Depends(get_db_session),
    _: IntegrationPrincipal = Depends(require_hiring_manager),
):
    return await _record_decision(candidate_ref, "rejected", db)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _analytics_get(c: CandidateMain, key: str):
    """Safely pull a field from resume_analysis.analytics on a CandidateMain row."""
    ra = c.resume_analysis or {}
    analytics = ra.get("analytics") or {}
    return analytics.get(key)


def _enrich_questions_with_answers(interview) -> list[dict]:
    """Combine InterviewQuestion rows with the per-question transcript snippet
    that Agent 5 stored in evaluation_data.answer_validation.
    """
    answer_map: dict[str, dict] = {}
    eval_data = interview.evaluation_data or {}
    for av in eval_data.get("answer_validation") or []:
        q_text = av.get("question") or ""
        if q_text:
            answer_map[q_text] = av
    return [
        {
            "question": q.question_text,
            "category": q.category,
            "difficulty": q.difficulty,
            "answer_quality": q.answer_quality,
            "score": q.answer_score,
            "answer_text": (answer_map.get(q.question_text, {}) or {}).get("answer"),
        }
        for q in interview.questions
    ]


def _candidate_summary(c: CandidateMain) -> dict:
    return {
        "candidate_ref": c.candidate_ref,
        "full_name": c.full_name,
        "current_title": c.current_title,
        "primary_domain": c.primary_domain,
        "readiness_score": c.readiness_score,
        "verification_status": c.verification_status,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


def _candidate_card(c: CandidateMain) -> dict:
    latest_interview = max(
        (i for i in c.interviews if i.overall_score is not None),
        key=lambda i: i.created_at,
        default=None,
    ) if c.interviews else None

    return {
        "candidate_ref": c.candidate_ref,
        "full_name": c.full_name,
        "current_title": c.current_title,
        "primary_domain": c.primary_domain,
        "total_experience_years": c.total_experience_years,
        "location": c.location,
        "readiness_score": c.readiness_score,
        "verification_status": c.verification_status,
        "resume_overall_score": c.resume_overall_score,
        "overall_score": latest_interview.overall_score if latest_interview else None,
        "l1_status": latest_interview.l1_status if latest_interview else None,
        "interview_ref": latest_interview.interview_ref if latest_interview else None,
        "github_url": c.github_url,
        "linkedin_url": c.linkedin_url,
        "current_ctc": c.current_ctc,
        "expected_ctc": c.expected_ctc,
        "notice_period": c.notice_period,
        "working_status": c.working_status,
        "preferred_location": c.preferred_location,
        "product_experience_years": _analytics_get(c, "product_experience_years"),
        "service_experience_years": _analytics_get(c, "service_experience_years"),
        "gcc_experience_years": _analytics_get(c, "gcc_experience_years"),
        "startup_experience_years": _analytics_get(c, "startup_experience_years"),
        "dominant_company_type": _analytics_get(c, "dominant_company_type"),
        "top_skills": [
            cs.skill.standard_name
            for cs in sorted(c.skills, key=lambda x: x.proficiency in ("EXPERT", "ADVANCED"), reverse=True)
            if cs.skill
        ][:6],
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }
