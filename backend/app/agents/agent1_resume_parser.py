"""Agent 1: Resume Parser — extracts structured profile from a resume file."""

import re
from datetime import date

from app.agents.prompts.agent1_prompt import AGENT1_SYSTEM_PROMPT
from app.core.clients.openai_client import chat_completion, vision_completion
from app.core.storage.local_storage import file_to_base64, read_file_bytes
from app.schemas.internal.agent_outputs import ResumeParseOutput
from app.utils.document_text import extract_text_from_docx, extract_text_from_pdf


_MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}


def _parse_date_string(s: str | None) -> tuple[int, int] | None:
    """Parse a free-form date string to (year, month). Returns None if unparseable.

    Handles: 'Nov 2024', '2024-11', 'November 2024', '2024/11', '11/2024', '2024'
    """
    if not s:
        return None
    s = s.strip()
    if not s or s.lower() in ("present", "current", "now", "today", "ongoing"):
        return None

    # ISO-ish: 2024-11, 2024/11, 11/2024
    iso = re.match(r"^(\d{4})[-/](\d{1,2})$", s)
    if iso:
        return int(iso.group(1)), int(iso.group(2))
    iso2 = re.match(r"^(\d{1,2})[-/](\d{4})$", s)
    if iso2:
        return int(iso2.group(2)), int(iso2.group(1))

    # Year only: '2024'
    if re.match(r"^\d{4}$", s):
        return int(s), 1

    # 'Nov 2024' or 'November 2024' or '2024 Nov'
    parts = re.split(r"[\s,/-]+", s)
    year = None
    month = None
    for p in parts:
        if p.isdigit() and len(p) == 4:
            year = int(p)
        elif p.lower() in _MONTHS:
            month = _MONTHS[p.lower()]
    if year is not None:
        return year, month or 1
    return None


def _months_between(start: tuple[int, int], end: tuple[int, int]) -> int:
    """Number of months between two (year, month) tuples, inclusive of partial months."""
    months = (end[0] - start[0]) * 12 + (end[1] - start[1])
    return max(months, 0)


def _recompute_durations(parsed: dict) -> dict:
    """Recompute duration_months for each experience entry based on parsed dates.
    Overrides the LLM's value when dates are parseable. Updates total_experience_years too.
    """
    today = date.today()
    today_tuple = (today.year, today.month)

    experiences = parsed.get("experience") or []
    total_months = 0
    for exp in experiences:
        start = _parse_date_string(exp.get("start_date"))
        end_raw = exp.get("end_date")
        end = _parse_date_string(end_raw)
        is_current = exp.get("is_current", False) or (end is None and end_raw)

        if start is None:
            # Can't parse — keep LLM's value
            total_months += exp.get("duration_months") or 0
            continue

        end_tuple = today_tuple if (end is None or is_current) else end
        months = _months_between(start, end_tuple)
        exp["duration_months"] = months
        total_months += months

    if experiences:
        parsed["total_experience_years"] = round(total_months / 12, 1)

    return parsed


_VALID_COMPANY_TYPES = {"PRODUCT", "SERVICE", "GCC", "STARTUP", "OTHER"}


def _recompute_company_type_years(parsed: dict) -> dict:
    """Recompute analytics.{product,service,gcc,startup}_experience_years from each
    experience entry's company_type + duration_months. Deterministic — overrides any
    LLM math the model produced.
    """
    experiences = parsed.get("experience") or []
    buckets: dict[str, int] = {t: 0 for t in _VALID_COMPANY_TYPES}

    for exp in experiences:
        ctype = (exp.get("company_type") or "OTHER").upper()
        if ctype not in _VALID_COMPANY_TYPES:
            ctype = "OTHER"
        exp["company_type"] = ctype  # normalize the case we wrote back
        buckets[ctype] += exp.get("duration_months") or 0

    analytics = parsed.setdefault("analysis", {}).setdefault("analytics", {})
    analytics["product_experience_years"] = round(buckets["PRODUCT"] / 12, 1)
    analytics["service_experience_years"] = round(buckets["SERVICE"] / 12, 1)
    analytics["gcc_experience_years"] = round(buckets["GCC"] / 12, 1)
    analytics["startup_experience_years"] = round(buckets["STARTUP"] / 12, 1)

    # Dominant type — order resolves ties (PRODUCT > GCC > STARTUP > SERVICE > OTHER)
    order = ["PRODUCT", "GCC", "STARTUP", "SERVICE", "OTHER"]
    dominant = max(order, key=lambda t: (buckets.get(t, 0), -order.index(t)))
    analytics["dominant_company_type"] = dominant if buckets.get(dominant, 0) > 0 else "OTHER"

    return parsed


async def parse_resume(file_path: str, content_type: str) -> ResumeParseOutput:
    """Parse a resume file and return structured candidate data."""
    today = date.today().strftime("%B %Y")  # e.g. "April 2026"
    system_prompt = AGENT1_SYSTEM_PROMPT + f"\n\nToday's date is {today}. Use this to calculate duration_months for current roles (end_date = 'Present')."

    is_image = content_type.startswith("image/")
    is_pdf = content_type == "application/pdf" or file_path.endswith(".pdf")
    is_docx = (
        content_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or file_path.endswith(".docx")
    )

    if is_image:
        b64 = file_to_base64(file_path)
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{content_type};base64,{b64}",
                            "detail": "high",
                        },
                    },
                    {
                        "type": "text",
                        "text": "Please extract all candidate information from this resume image.",
                    },
                ],
            },
        ]
        raw = await vision_completion(messages)
    else:
        file_bytes = read_file_bytes(file_path)
        if is_pdf:
            text = extract_text_from_pdf(file_bytes)
        elif is_docx:
            text = extract_text_from_docx(file_bytes)
        else:
            text = file_bytes.decode("utf-8", errors="ignore")

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Parse the following resume text and extract structured data:\n\n{text}",
            },
        ]
        raw = await chat_completion(messages)

    raw = _recompute_durations(raw)
    raw = _recompute_company_type_years(raw)
    return ResumeParseOutput.model_validate(raw)
