"""Local file storage utilities."""

import base64
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config.settings import get_settings


def _upload_dir(category: str) -> Path:
    settings = get_settings()
    directory = Path(settings.local_storage_path) / category
    directory.mkdir(parents=True, exist_ok=True)
    return directory


async def save_upload(file: UploadFile, category: str) -> tuple[str, str]:
    """Save an uploaded file to local storage.

    Returns (absolute_path, stored_filename).
    """
    suffix = Path(file.filename or "file").suffix
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    directory = _upload_dir(category)
    dest = directory / stored_name

    contents = await file.read()
    dest.write_bytes(contents)

    return str(dest), stored_name


def read_file_bytes(path: str) -> bytes:
    """Read a file from local storage and return its bytes."""
    return Path(path).read_bytes()


def file_to_base64(path: str) -> str:
    """Read a file and return its Base64-encoded string (no data-URI prefix)."""
    return base64.b64encode(read_file_bytes(path)).decode("utf-8")
