"""Coresignal Employee API client — fetches public LinkedIn profile data for cross-check.

Abstracted as a `LinkedInProvider` so we can swap to Proxycurl/BrightData later
by adding a sibling implementation without changing callers.

Coresignal Employee Multi-source API (v2) endpoint reference:
  - Lookup by LinkedIn URL:  GET  {base}/employee_multi_source/collect/{linkedin_shorthand_name}
    where linkedin_shorthand_name is the `/in/<name>` slug from the LinkedIn URL.
  - Auth header: `apikey: <CORESIGNAL_API_KEY>`
  - See https://docs.coresignal.com/ for current spec.
"""

from __future__ import annotations

import re
from typing import Any

import httpx
import structlog

from app.config.settings import get_settings

logger = structlog.get_logger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# URL helpers
# ──────────────────────────────────────────────────────────────────────────────

_LINKEDIN_SLUG_RE = re.compile(r"linkedin\.com/in/([^/?#]+)", re.IGNORECASE)


def _extract_linkedin_slug(linkedin_url: str) -> str | None:
    """Return the `/in/<slug>` value from a LinkedIn URL.

    Accepts: https://www.linkedin.com/in/janedoe/
             linkedin.com/in/janedoe
             https://linkedin.com/in/jane-doe-12345
    """
    if not linkedin_url:
        return None
    m = _LINKEDIN_SLUG_RE.search(linkedin_url.strip())
    if not m:
        return None
    return m.group(1).strip().lower()


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

class LinkedInLookupError(Exception):
    """Raised when the upstream provider returns an unrecoverable error."""


async def fetch_linkedin_profile(linkedin_url: str) -> dict[str, Any] | None:
    """Fetch a candidate's LinkedIn profile data via Coresignal.

    Returns a normalized dict with `experiences`, `educations`, `name`, `headline`.
    Returns None if the API key is not configured, the URL can't be parsed,
    or the profile is not found (404).

    Raises LinkedInLookupError on auth/quota/server errors so the caller can
    distinguish "not found" (None) from "provider down" (exception).
    """
    settings = get_settings()
    api_key = settings.coresignal_api_key.get_secret_value()
    if not api_key:
        logger.warning("coresignal.disabled", reason="no api key configured")
        return None

    slug = _extract_linkedin_slug(linkedin_url)
    if not slug:
        logger.warning("coresignal.invalid_url", url=linkedin_url)
        return None

    url = f"{settings.coresignal_base_url.rstrip('/')}/employee_multi_source/collect/{slug}"
    headers = {
        "apikey": api_key,
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=settings.coresignal_timeout_seconds) as client:
            resp = await client.get(url, headers=headers)
    except httpx.HTTPError as exc:
        logger.error("coresignal.request_failed", error=str(exc))
        raise LinkedInLookupError(f"Coresignal request failed: {exc}") from exc

    if resp.status_code == 404:
        logger.info("coresignal.profile_not_found", slug=slug)
        return None
    if resp.status_code == 401 or resp.status_code == 403:
        raise LinkedInLookupError(f"Coresignal auth error ({resp.status_code}): {resp.text[:200]}")
    if resp.status_code == 429:
        raise LinkedInLookupError("Coresignal rate limit / quota exceeded")
    if resp.status_code >= 500:
        raise LinkedInLookupError(f"Coresignal server error {resp.status_code}")
    if resp.status_code >= 400:
        raise LinkedInLookupError(f"Coresignal error {resp.status_code}: {resp.text[:200]}")

    try:
        raw = resp.json()
    except ValueError as exc:
        raise LinkedInLookupError(f"Coresignal returned non-JSON: {exc}") from exc

    return _normalize_coresignal_profile(raw)


# ──────────────────────────────────────────────────────────────────────────────
# Normalization — map Coresignal's response into a stable shape for the LLM diff
# ──────────────────────────────────────────────────────────────────────────────

def _normalize_coresignal_profile(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize a Coresignal employee record to a stable shape.

    Coresignal's response includes many fields; we keep only what we need for the
    cross-check (name, headline, experiences with company/title/dates).
    Field names from Coresignal can vary across schema versions — we defensively
    look in common locations.
    """
    name = (
        raw.get("name")
        or raw.get("full_name")
        or f"{raw.get('first_name', '')} {raw.get('last_name', '')}".strip()
    )

    experiences: list[dict[str, Any]] = []
    for item in raw.get("experience") or raw.get("experiences") or raw.get("member_experience_collection") or []:
        experiences.append({
            "company": item.get("company_name") or item.get("company") or "",
            "title": item.get("title") or item.get("position_title") or "",
            "start_date": item.get("date_from") or item.get("start_date") or "",
            "end_date": item.get("date_to") or item.get("end_date") or "",
            "is_current": bool(item.get("is_current") or item.get("current")),
        })

    educations: list[dict[str, Any]] = []
    for item in raw.get("education") or raw.get("educations") or raw.get("member_education_collection") or []:
        educations.append({
            "institution": item.get("school_name") or item.get("institution") or "",
            "degree": item.get("degree") or "",
            "field": item.get("field_of_study") or item.get("field") or "",
        })

    return {
        "name": name,
        "headline": raw.get("headline") or raw.get("title") or "",
        "experiences": experiences,
        "educations": educations,
    }
