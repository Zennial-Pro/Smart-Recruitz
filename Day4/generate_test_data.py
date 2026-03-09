import os
import asyncio
from fpdf import FPDF
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

def create_pdf(text: str, filename: str):
    """Creates a PDF file from the given text."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    
    # Handle utf-8 characters by replacing non-latin-1 or using a different approach
    # For simplicity, we encode and decode ignoring errors
    safe_text = text.encode('latin-1', 'replace').decode('latin-1')
    
    pdf.multi_cell(0, 5, safe_text)
    
    output_path = os.path.join(os.path.dirname(__file__), "test_transcripts", filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)
    print(f"Created PDF: {output_path}")

async def generate_transcript(llm, prompt: str, filename: str):
    """Uses Gemini to generate a single synthetic transcript."""
    print(f"Generating synthetic transcript for {filename}...")
    try:
        response = llm.invoke([
            SystemMessage(content="You are an AI that writes excellent mock interview transcripts for testing AI systems."),
            HumanMessage(content=prompt)
        ])
        
        transcript_text = response.content
        create_pdf(transcript_text, filename)
        
    except Exception as e:
        print(f"Failed to generate transcript {filename}: {e}")

async def generate_batch():
    """Generates a batch of transcripts with varying lengths."""
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
    
    # Define a base prompt structure
    base_instructions = """
    Please generate a realistic mock interview transcript for a 'Senior Backend Engineer' position.
    Include the Q&A format explicitly mapping "Interviewer:" and "Candidate:".
    
    CRITICAL:
    Include Personally Identifiable Information (PII) for the candidate as the first thing they say when asked to introduce themselves.
    Make sure they state their name, their email address, and their phone number.
    """
    
    prompts = [
        # Transcript 1: Short (intentionally < 5 pairs to trigger rejection)
        (
            base_instructions + "\n" + 
            "Make this transcript very short. EXACTLY 3 Q&A pairs (one standard question, one short answer, then the call drops)."
        ),
        # Transcript 2: Incomplete question
        (
            base_instructions + "\n" + 
            "Make this transcript comprehensive. AT LEAST 6 Q&A pairs. \n" +
            "Include a scenario where the interviewer asks an incomplete question and the candidate is confused, then the interviewer clarifies."
        ),
        # Transcript 3: Incomplete answer
        (
            base_instructions + "\n" + 
            "Make this transcript comprehensive. AT LEAST 6 Q&A pairs. \n" +
            "The candidate constantly gives incomplete answers and gets cut off or distracted before finishing their point."
        ),
        # Transcript 4: Very good answers
        (
            base_instructions + "\n" + 
            "Make this transcript comprehensive. AT LEAST 6 Q&A pairs. \n" +
            "The candidate should give strong, detailed, very good answers for every question."
        ),
        # Transcript 5: Unrelated answers
        (
            base_instructions + "\n" + 
            "Make this transcript comprehensive. AT LEAST 6 Q&A pairs. \n" +
            "The candidate completely misunderstands and gives unrelated, off-topic answers to technical questions."
        ),
        # Transcript 6: Very superficial answers
        (
            base_instructions + "\n" + 
            "Make this transcript comprehensive. AT LEAST 6 Q&A pairs. \n" +
            "The candidate uses lots of buzzwords but gives extremely superficial answers with no technical depth."
        ),
        # Transcript 7: Deep knowledge answers
        (
            base_instructions + "\n" + 
            "Make this transcript comprehensive. AT LEAST 6 Q&A pairs. \n" +
            "The candidate demonstrates extremely deep expert-level understanding of System Design and Python internals."
        ),
        # Transcript 8: Polite but doesn't know
        (
            base_instructions + "\n" + 
            "Make this transcript comprehensive. AT LEAST 6 Q&A pairs. \n" +
            "The candidate is very polite but honestly admits they don't know the answer to most of the technical questions."
        ),
        # Transcript 9: Mixed - strong on one topic, weak on another
        (
            base_instructions + "\n" + 
            "Make this transcript comprehensive. AT LEAST 6 Q&A pairs. \n" +
            "The candidate is excellent at Python API development, but terrible at databases and System Design."
        ),
        # Transcript 10: Standard mid-level
        (
            base_instructions + "\n" + 
            "Make this transcript comprehensive. AT LEAST 6 Q&A pairs. \n" +
            "The candidate gives standard mid-level answers, getting some things right and making a few minor mistakes."
        ),
    ]
    
    for i, prompt in enumerate(prompts):
        filename = f"transcript_{i+1:02d}.pdf"
        await generate_transcript(llm, prompt, filename)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Always override environment with the new working key
    os.environ["GOOGLE_API_KEY"] = "AIzaSyAaA0Z15afin6U2YyoqsCBlq9K51iyDf3I"
        
    asyncio.run(generate_batch())
