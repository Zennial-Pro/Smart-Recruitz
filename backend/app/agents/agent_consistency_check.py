"""Consistency Check — diff resume experience vs LinkedIn experience."""

import json

from app.agents.prompts.agent_consistency_prompt import AGENT_CONSISTENCY_SYSTEM_PROMPT
from app.core.clients.openai_client import chat_completion
from app.schemas.internal.agent_outputs import ConsistencyCheckOutput


async def cross_check_linkedin(
    resume_experiences: list[dict],
    linkedin_profile: dict | None,
) -> ConsistencyCheckOutput:
    """Compare resume work history against LinkedIn work history via an LLM.

    Short-circuits with a clear "no LinkedIn data" result when the provider
    returned nothing — no LLM call wasted.
    """
    if not linkedin_profile or not (linkedin_profile.get("experiences") or []):
        return ConsistencyCheckOutput(
            match_score=0,
            consistent=False,
            summary="LinkedIn profile not found or returned no work history.",
            mismatches=[],
        )

    payload = {
        "resume_experience": resume_experiences,
        "linkedin_experience": linkedin_profile.get("experiences", []),
        "linkedin_headline": linkedin_profile.get("headline", ""),
    }

    messages = [
        {"role": "system", "content": AGENT_CONSISTENCY_SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(payload, default=str, indent=2)},
    ]

    raw = await chat_completion(messages)
    return ConsistencyCheckOutput.model_validate(raw)
