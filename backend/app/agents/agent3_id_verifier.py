"""Agent 3: ID Verifier — verifies identity documents via vision."""

import base64
import io

from app.agents.prompts.agent3_prompt import AGENT3_SYSTEM_PROMPT
from app.core.clients.openai_client import vision_completion
from app.core.storage.local_storage import file_to_base64, read_file_bytes
from app.schemas.internal.agent_outputs import VerificationOutput


def _pdf_to_image_b64(file_path: str) -> tuple[str, str]:
    """Convert first page of PDF to PNG base64. Returns (b64, mime_type)."""
    import fitz  # pymupdf
    doc = fitz.open(file_path)
    page = doc[0]
    mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for clarity
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    return base64.b64encode(img_bytes).decode(), "image/png"


async def verify_identity(
    file_path: str,
    content_type: str,
    document_type: str,
    claimed_name: str,
) -> VerificationOutput:
    """Verify an ID document using GPT-4o mini vision."""

    is_pdf = content_type == "application/pdf" or file_path.endswith(".pdf")
    if is_pdf:
        b64, mime = _pdf_to_image_b64(file_path)
    else:
        b64, mime = file_to_base64(file_path), content_type

    messages = [
        {"role": "system", "content": AGENT3_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime};base64,{b64}",
                        "detail": "high",
                    },
                },
                {
                    "type": "text",
                    "text": (
                        f"Document type: {document_type}\n"
                        f"Claimed name: {claimed_name}\n\n"
                        "Please verify this identity document and extract its data."
                    ),
                },
            ],
        },
    ]

    raw = await vision_completion(messages)
    # Ensure document_type is set
    if "document_type" not in raw or not raw["document_type"]:
        raw["document_type"] = document_type

    return VerificationOutput.model_validate(raw)
