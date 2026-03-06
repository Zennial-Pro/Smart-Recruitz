"""
app/agents/interview_validation/nodes/score_answers.py
"""
from typing import Any, Dict
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_anthropic import ChatAnthropic
from app.core.logging import get_logger
from app.core.config import settings
from app.agents.interview_validation.state import InterviewValidationState
from app.agents.interview_validation.prompts import PromptBuilder, parse_llm_response

logger = get_logger(__name__)

# Configured Claude Model
MODEL_NAME = "claude-3-5-sonnet-20241022"

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
async def _call_claude_with_retry(prompt: str) -> str:
    """Call Claude LLM with tenacity retry logic."""
    llm = ChatAnthropic(
        model_name=MODEL_NAME,
        anthropic_api_key=settings.ANTHROPIC_API_KEY,
        temperature=0.0,
        max_tokens=2000
    )
    response = await llm.ainvoke(prompt)
    return response.content if hasattr(response, "content") else str(response)

async def score_answers_node(state: InterviewValidationState) -> Dict[str, Any]:
    """Score the interview answers using Claude.

    Args:
        state: The current state.

    Returns:
        State updates containing answer evaluations and dimension scores.
    """
    logger.info(
        "node_started",
        node="score_answers",
        request_id=state.get("interview_id", "unknown")
    )

    updates: Dict[str, Any] = {}

    try:
        if state.get("errors"):
            return updates

        position = state.get("position", "")
        transcript = state.get("pii_stripped_transcript", state.get("transcript", ""))
        questions_with_rubric = state.get("questions_with_rubric", [])

        prompt = PromptBuilder.build_scoring_prompt(
            position=position,
            transcript=transcript,
            questions_with_rubric=questions_with_rubric
        )

        response_text = await _call_claude_with_retry(prompt)
        parsed_json = parse_llm_response(response_text)

        updates["answer_evaluations"] = parsed_json.get("answer_evaluations", [])
        updates["dimension_scores"] = parsed_json.get("dimension_scores", {})
        updates["audit_trail"] = [{"node": "score_answers", "status": "success", "details": "Answers scored successfully"}]

    except Exception as e:
        logger.error("operation_failed", error=str(e), exc_info=True)
        updates["errors"] = [f"score_answers error: {str(e)}"]
        updates["audit_trail"] = [{"node": "score_answers", "status": "failed", "details": str(e)}]

    return updates
