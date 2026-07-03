"""Agent 2: Duplicate Detector — checks if a candidate already exists."""

import json

from app.agents.prompts.agent2_prompt import AGENT2_SYSTEM_PROMPT
from app.core.clients.openai_client import chat_completion
from app.schemas.internal.agent_outputs import DuplicateCheckOutput


async def check_duplicate(
    candidate: dict,
    potential_matches: list[dict],
) -> DuplicateCheckOutput:
    """Compare candidate against potential duplicates from the DB.

    If no potential matches, short-circuit without calling the LLM.
    """
    if not potential_matches:
        return DuplicateCheckOutput(
            result="UNIQUE",
            confidence=0.99,
            matched_candidate_ref=None,
            reasoning="No similar candidates found in the database.",
        )

    matches_json = json.dumps(potential_matches, indent=2, default=str)
    candidate_json = json.dumps(candidate, indent=2, default=str)

    messages = [
        {"role": "system", "content": AGENT2_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"New candidate:\n{candidate_json}\n\n"
                f"Potential matches from database:\n{matches_json}\n\n"
                "Determine if the new candidate is a duplicate."
            ),
        },
    ]

    raw = await chat_completion(messages)
    return DuplicateCheckOutput.model_validate(raw)
