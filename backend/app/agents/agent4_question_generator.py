"""Agent 4: Interview Question Generator."""

import json
import uuid

from app.agents.prompts.agent4_prompt import AGENT4_SYSTEM_PROMPT
from app.core.clients.openai_client import chat_completion
from app.schemas.internal.agent_outputs import QuestionsOutput


async def generate_questions(
    candidate_profile: dict,
    previous_questions: list[str] | None = None,
) -> QuestionsOutput:
    """Generate personalized interview questions for a candidate."""

    profile_json = json.dumps(candidate_profile, indent=2, default=str)

    user_content = f"Generate 2 interview questions for this candidate:\n\n{profile_json}"

    if previous_questions:
        prev_list = "\n".join(f"- {q}" for q in previous_questions)
        user_content += (
            f"\n\nDo NOT repeat or rephrase any of these previously asked questions:\n{prev_list}"
        )

    messages = [
        {"role": "system", "content": AGENT4_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    raw = await chat_completion(messages)

    # Inject interview_ref if not present (will be overwritten by handler with the real ref)
    if "interview_ref" not in raw:
        raw["interview_ref"] = f"INT-{uuid.uuid4().hex[:8].upper()}"

    return QuestionsOutput.model_validate(raw)
