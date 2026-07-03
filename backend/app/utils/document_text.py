"""Shared helpers for extracting plain text from uploaded documents.

Used by Agent 1 (resume parser) and the hiring-manager JD extractor.
"""

import io


def extract_text_from_pdf(file_bytes: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(para.text for para in doc.paragraphs).strip()


def extract_text(file_bytes: bytes, content_type: str | None, filename: str | None = None) -> str:
    """Dispatch to the right extractor based on content_type/filename.

    Falls back to UTF-8 decoding for unknown types. Returns the raw extracted
    text (whitespace normalized but not chunked).
    """
    ct = (content_type or "").lower()
    name = (filename or "").lower()

    is_pdf = ct == "application/pdf" or name.endswith(".pdf")
    is_docx = (
        ct == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or name.endswith(".docx")
    )

    if is_pdf:
        return extract_text_from_pdf(file_bytes)
    if is_docx:
        return extract_text_from_docx(file_bytes)
    return file_bytes.decode("utf-8", errors="ignore").strip()
