"""JD Extractor — parses a job description into structured hiring criteria.

One LLM call. Returns required vs preferred skills, role level, experience floor,
and a one-line summary. Powers the hiring-manager search auto-fill.
"""

from app.agents.prompts.jd_extraction_prompt import JD_EXTRACTION_SYSTEM_PROMPT
from app.core.clients.openai_client import chat_completion
from app.schemas.internal.agent_outputs import JDExtractionOutput


# Safety bound — if the JD is enormous we trim to keep the prompt practical.
MAX_JD_CHARS = 12000


async def extract_jd(jd_text: str) -> JDExtractionOutput:
    """Run the LLM extraction pass over a JD text blob."""
    text = (jd_text or "").strip()
    if not text:
        return JDExtractionOutput()

    if len(text) > MAX_JD_CHARS:
        text = text[:MAX_JD_CHARS]

    messages = [
        {"role": "system", "content": JD_EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": f"Extract structured criteria from this JD:\n\n{text}"},
    ]
    raw = await chat_completion(messages)
    # The LLM may still return a `required_skills` key from cached prompts/old training —
    # drop it before validation so it doesn't slip through. Two-bucket schema only.
    if isinstance(raw, dict) and "required_skills" in raw:
        # Promote any straggler entries into mandatory_skills if mandatory was empty,
        # else into preferred_skills.
        leftover = raw.pop("required_skills", []) or []
        if not raw.get("mandatory_skills"):
            raw["mandatory_skills"] = leftover
        else:
            raw["preferred_skills"] = list(raw.get("preferred_skills") or []) + leftover
    parsed = JDExtractionOutput.model_validate(raw)

    # Drop empties
    parsed.mandatory_skills = [s for s in parsed.mandatory_skills if s.strip()]
    parsed.preferred_skills = [s for s in parsed.preferred_skills if s.strip()]

    # Defensive dedup — mandatory wins over preferred.
    mand_lower = {s.lower() for s in parsed.mandatory_skills}
    parsed.preferred_skills = [s for s in parsed.preferred_skills if s.lower() not in mand_lower]

    return parsed
