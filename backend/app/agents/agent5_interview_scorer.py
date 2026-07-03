"""Agent 5: Interview Scorer — scores candidate responses against expected answers."""

import json

from app.agents.prompts.agent5_prompt import AGENT5_SYSTEM_PROMPT
from app.core.clients.openai_client import chat_completion
from app.schemas.internal.agent_outputs import ScoringOutput


async def score_interview(
    transcript: str,
    questions: list[dict],
) -> ScoringOutput:
    """Score a candidate's interview transcript against generated questions."""

    questions_json = json.dumps(questions, indent=2, default=str)

    messages = [
        {"role": "system", "content": AGENT5_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Interview questions with expected answers:\n{questions_json}\n\n"
                f"Candidate's interview transcript:\n{transcript}\n\n"
                "Score the candidate's performance."
            ),
        },
    ]

    raw = await chat_completion(messages)
    return ScoringOutput.model_validate(raw)
