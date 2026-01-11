"""
⚠️ STARTERPACK CORE — DO NOT MODIFY
File upload utilities with secure validation.
"""

import os
import uuid
from pathlib import Path

import magic
from fastapi import HTTPException, UploadFile

from .logging import get_logger

logger = get_logger(__name__)

STATIC_DIR = Path("/app/static")


class FileValidationError(HTTPException):
    """Raised when file validation fails."""

    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


async def save_uploaded_file(
    file: UploadFile,
    allowed_types: list[str],
    max_size_mb: float = 5,
    subdirectory: str = "uploads",
) -> str:
    """
    Validates and saves an uploaded file securely.

    Args:
        file: The uploaded file from FastAPI
        allowed_types: List of allowed MIME types (e.g., ["image/jpeg", "image/png"])
        max_size_mb: Maximum file size in megabytes (default: 5MB)
        subdirectory: Subdirectory within /static/ to save files (default: "uploads")

    Returns:
        Public URL path to the saved file (e.g., "/static/uploads/uuid.jpg")

    Raises:
        FileValidationError: If file fails validation (type, size)
    """
    # Read file content
    content = await file.read()
    await file.seek(0)

    # Validate file size
    max_size_bytes = int(max_size_mb * 1024 * 1024)
    if len(content) > max_size_bytes:
        raise FileValidationError(f"File exceeds maximum size of {max_size_mb}MB")

    # Validate MIME type using magic bytes (not extension)
    detected_type = magic.from_buffer(content, mime=True)
    if detected_type not in allowed_types:
        raise FileValidationError(
            f"File type '{detected_type}' not allowed. Allowed types: {', '.join(allowed_types)}"
        )

    # Generate safe filename with UUID
    original_ext = _get_extension_for_mime(detected_type, file.filename)
    safe_filename = f"{uuid.uuid4()}{original_ext}"

    # Ensure target directory exists
    target_dir = STATIC_DIR / subdirectory
    target_dir.mkdir(parents=True, exist_ok=True)

    # Save file
    file_path = target_dir / safe_filename
    with open(file_path, "wb") as f:
        f.write(content)

    logger.info(
        "File uploaded",
        filename=safe_filename,
        mime_type=detected_type,
        size_bytes=len(content),
        subdirectory=subdirectory,
    )

    # Return public URL path
    return f"/static/{subdirectory}/{safe_filename}"


def _get_extension_for_mime(mime_type: str, original_filename: str | None) -> str:
    """
    Get file extension for a MIME type.
    Falls back to original filename extension if available.
    """
    mime_to_ext = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
        "application/pdf": ".pdf",
        "text/plain": ".txt",
        "text/csv": ".csv",
        "application/json": ".json",
    }

    if mime_type in mime_to_ext:
        return mime_to_ext[mime_type]

    # Fall back to original extension if available
    if original_filename:
        _, ext = os.path.splitext(original_filename)
        if ext:
            return ext.lower()

    return ""


async def delete_uploaded_file(url_path: str) -> bool:
    """
    Delete a previously uploaded file by its URL path.

    Args:
        url_path: The URL path returned by save_uploaded_file (e.g., "/static/uploads/uuid.jpg")

    Returns:
        True if file was deleted, False if file didn't exist
    """
    if not url_path.startswith("/static/"):
        raise FileValidationError("Invalid file path")

    # Convert URL path to filesystem path
    relative_path = url_path.replace("/static/", "", 1)
    file_path = STATIC_DIR / relative_path

    # Security: ensure path is within STATIC_DIR (prevent path traversal)
    try:
        file_path.resolve().relative_to(STATIC_DIR.resolve())
    except ValueError as err:
        raise FileValidationError("Invalid file path") from err

    if file_path.exists():
        file_path.unlink()
        logger.info("File deleted", path=url_path)
        return True

    return False
