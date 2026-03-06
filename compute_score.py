"""
app/agents/interview_validation/nodes/compute_score.py
"""
from typing import Any, Dict
from app.core.logging import get_logger
from app.models.interview_validation import ReadinessLevel, L1Status
from app.agents.interview_validation.state import InterviewValidationState

logger = get_logger(__name__)

async def compute_score_node(state: InterviewValidationState) -> Dict[str, Any]:
    """Compute the overall score and readiness tier.

    Args:
        state: The current state of the interview validation agent.

    Returns:
        Dictionary containing state updates.
    """
    logger.info(
        "node_started",
        node="compute_score",
        request_id=state.get("interview_id", "unknown")
    )

    updates: Dict[str, Any] = {}

    try:
        if state.get("errors"):
            return updates

        dimension_scores = state.get("dimension_scores", {})
        technical = dimension_scores.get("technical", 0.0)
        experience = dimension_scores.get("experience", 0.0)
        communication = dimension_scores.get("communication", 0.0)

        overall_score = (technical * 0.40) + (experience * 0.35) + (communication * 0.25)
        overall_score = round(overall_score, 2)

        updates["overall_score"] = overall_score

        if overall_score >= 80:
            updates["readiness_level"] = ReadinessLevel.HIGH_READY.value
            updates["l1_status"] = L1Status.PASSED.value
        elif overall_score >= 60:
            updates["readiness_level"] = ReadinessLevel.INTERVIEW_READY.value
            updates["l1_status"] = L1Status.PASSED.value
        elif overall_score >= 55:
            updates["readiness_level"] = ReadinessLevel.BORDERLINE.value
            updates["l1_status"] = L1Status.BORDERLINE.value
        else:
            updates["readiness_level"] = ReadinessLevel.FAILED.value
            updates["l1_status"] = L1Status.FAILED.value

        updates["audit_trail"] = [{"node": "compute_score", "status": "success", "details": f"Score computed: {overall_score}"}]

    except Exception as e:
        logger.error("operation_failed", error=str(e), exc_info=True)
        updates["errors"] = [f"compute_score error: {str(e)}"]
        updates["audit_trail"] = [{"node": "compute_score", "status": "failed", "details": str(e)}]

    return updates
