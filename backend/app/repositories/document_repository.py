"""CRUD operations for UploadedDocument."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.uploaded_document import UploadedDocument


async def create_document(
    db: AsyncSession,
    filename: str,
    storage_path: str,
    content_type: str,
    file_size_bytes: int,
    document_category: str,
    uploaded_by_ref: str,
) -> UploadedDocument:
    doc = UploadedDocument(
        filename=filename,
        original_filename=filename,
        content_type=content_type,
        file_size_bytes=file_size_bytes,
        storage_path=storage_path,
        document_category=document_category,
        uploaded_by_ref=uploaded_by_ref,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return doc
