import logging
import asyncio
from app.agents.interview_validation.workflow import InterviewValidationAgent
from app.agents.interview_validation.nodes.mock_score_answers import mock_score_answers_node

logger = logging.getLogger(__name__)

async def run_e2e_test():
    """
    Runs an end-to-end test of the Day 3 workflow with mock AI.
    """
    # Correct way to test with mock: Just invoke the nodes or re-compile a test graph
    from langgraph.graph import StateGraph, END
    from app.agents.interview_validation.state import InterviewValidationState
    from app.agents.interview_validation.nodes.validate_input import validate_input_node
    from app.agents.interview_validation.nodes.strip_pii import strip_pii_node
    from app.agents.interview_validation.nodes.compute_score import compute_score_node
    from app.agents.interview_validation.nodes.talent_pool_gate import talent_pool_gate_node
    from app.agents.interview_validation.nodes.finalize import finalize_node

    test_workflow = StateGraph(InterviewValidationState)
    test_workflow.add_node("validate_input", validate_input_node)
    test_workflow.add_node("strip_pii", strip_pii_node)
    test_workflow.add_node("score_answers", mock_score_answers_node) # USE MOCK
    test_workflow.add_node("compute_score", compute_score_node)
    test_workflow.add_node("talent_pool_gate", talent_pool_gate_node)
    test_workflow.add_node("finalize", finalize_node)
    
    test_workflow.set_entry_point("validate_input")
    test_workflow.add_edge("validate_input", "strip_pii")
    test_workflow.add_edge("strip_pii", "score_answers")
    test_workflow.add_edge("score_answers", "compute_score")
    test_workflow.add_edge("compute_score", "talent_pool_gate")
    test_workflow.add_edge("talent_pool_gate", "finalize")
    test_workflow.add_edge("finalize", END)
    
    test_agent = test_workflow.compile()
    
    sample_input = {
        "interview_id": "test-123",
        "candidate_id": "cand-456",
        "position": "Senior Backend Engineer",
        "interview_type": "L1_SCREENING",
        "transcript": "Q: Tell me about FastAPI. A: FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints. " * 30, # ~300 words
        "questions_with_rubric": [{"question": "FastAPI experience", "rubric": "Score based on async knowledge"}]
    }
    
    print("Running E2E Integration Test...")
    result = await test_agent.ainvoke(sample_input)
    print("\nTest Result:")
    print(f"Overall Score: {result['overall_score']}")
    print(f"Readiness Level: {result['readiness_level']}")
    print(f"Action: {result['talent_pool_action']}")
    print(f"PII Stripped: {'[STRIPPED' in result.get('pii_stripped_transcript', '')}")
    
    return result

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
