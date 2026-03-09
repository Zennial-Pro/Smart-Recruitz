import logging
import asyncio
from app.agents.interview_validation.workflow import InterviewValidationAgent
from app.agents.interview_validation.nodes.gemini_score_answers import gemini_score_answers_node

logger = logging.getLogger(__name__)

async def run_e2e_test(test_agent):
    """
    Runs an end-to-end test of the Day 3 workflow with real Gemini AI.
    """
    import os
    from PyPDF2 import PdfReader

    os.environ["GOOGLE_API_KEY"] = "AIzaSyAaA0Z15afin6U2YyoqsCBlq9K51iyDf3I"

    print("Reading synthetic transcript from PDF...")
    pdf_path = os.path.join(os.path.dirname(__file__), "test_transcripts", "transcript_04.pdf")
    try:
        reader = PdfReader(pdf_path)
        transcript_text = ""
        for page in reader.pages:
            transcript_text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading transcript: {e}")
        transcript_text = "Error reading transcript."

    sample_input = {
        "interview_id": "test-123",
        "candidate_id": "cand-456",
        "position": "Senior Backend Engineer",
        "interview_type": "L1_SCREENING",
        "transcript": transcript_text,
        "questions_with_rubric": [
            {"question": "Python frameworks", "rubric": "Score based on technical depth"},
            {"question": "System Design", "rubric": "Score based on architectural choices"}
        ]
    }
    
    print("Running E2E Integration Test...")
    result = await test_agent.ainvoke(sample_input)
    print("\nTest Result:")
    print(f"Overall Score: {result['overall_score']}")
    print(f"Readiness Level: {result['readiness_level']}")
    print(f"Action: {result['talent_pool_action']}")
    print(f"PII Stripped: {'[STRIPPED' in result.get('pii_stripped_transcript', '')}")
    
    return result

async def run_negative_tests(test_agent):
    """
    Runs edge cases to verify how the graph handles bad data.
    """
    print("\n--- Running Negative Test Cases ---\n")
    
    # 1. The Empty Transcript Failure
    print("Test 1: Empty Transcript String")
    sample_empty_input = {
        "interview_id": "test-empty",
        "candidate_id": "cand-999",
        "position": "Backend Engineer",
        "interview_type": "L1_SCREENING",
        "transcript": "", # <--- THIS CAUSES THE CRASH
        "questions_with_rubric": [{"question": "Experience", "rubric": "Score 1-10"}]
    }
    try:
        await test_agent.ainvoke(sample_empty_input)
    except Exception as e:
        print(f"FAILED (Expected): Pipeline crashed on empty transcript! Error: {str(e)[:50]}...")

    # 2. The Missing Rubric Error
    print("\nTest 2: Missing HR Rubric")
    sample_no_rubric_input = {
        "interview_id": "test-norubric",
        "candidate_id": "cand-888",
        "position": "Senior Dev",
        "interview_type": "L1_SCREENING",
        "transcript": "Q: Tell me about yourself. A: I am a dev.",
        "questions_with_rubric": [] # <--- HR FORGOT TO ADD RUBRICS
    }
    try:
        result = await test_agent.ainvoke(sample_no_rubric_input)
        print("FAILED (Expected): AI hallucinates scores because rubric was missing!")
        if float(result.get('overall_score', 0)) > 80:
            print(" -> DANGER: Candidate was marked HIGH_READY based on AI hallucination!")
    except Exception as e:
        print(f"FAILED: Pipeline crashed unexpectedly {e}")

if __name__ == "__main__":
    # Get the compiled agent from the main function
    from app.agents.interview_validation.workflow import InterviewValidationAgent
    from app.agents.interview_validation.nodes.gemini_score_answers import gemini_score_answers_node
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
    test_workflow.add_node("score_answers", gemini_score_answers_node) 
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
    
    # Run original test
    asyncio.run(run_e2e_test(test_agent))
    
    # Run the new negative cases to show them failing
    asyncio.run(run_negative_tests(test_agent))

