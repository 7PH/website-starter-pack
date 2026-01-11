# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""
Tests for file upload utility.
"""

import io

import pytest
from fastapi import UploadFile

from src.helpers.file_upload import (
    FileValidationError,
    delete_uploaded_file,
    save_uploaded_file,
)


class TestSaveUploadedFile:
    """Tests for save_uploaded_file function."""

    async def test_saves_valid_jpeg(self, temp_static_dir, sample_image_bytes):
        """Valid JPEG should be saved and return URL path."""
        file = UploadFile(
            filename="test.jpg",
            file=io.BytesIO(sample_image_bytes),
        )

        url = await save_uploaded_file(
            file=file,
            allowed_types=["image/jpeg"],
            subdirectory="images",
        )

        # Should return valid URL path
        assert url.startswith("/static/images/")
        assert url.endswith(".jpg")

        # File should exist on disk
        file_path = temp_static_dir / url.replace("/static/", "")
        assert file_path.exists()

    async def test_saves_valid_png(self, temp_static_dir, sample_png_bytes):
        """Valid PNG should be saved and return URL path."""
        file = UploadFile(
            filename="test.png",
            file=io.BytesIO(sample_png_bytes),
        )

        url = await save_uploaded_file(
            file=file,
            allowed_types=["image/png"],
            subdirectory="images",
        )

        assert url.startswith("/static/images/")
        assert url.endswith(".png")

    async def test_rejects_invalid_mime_type(self, temp_static_dir, sample_text_bytes):
        """Text file disguised as image should be rejected."""
        file = UploadFile(
            filename="fake.jpg",  # Fake extension
            file=io.BytesIO(sample_text_bytes),
        )

        with pytest.raises(FileValidationError) as exc:
            await save_uploaded_file(
                file=file,
                allowed_types=["image/jpeg", "image/png"],
            )

        assert "not allowed" in str(exc.value.detail)

    async def test_rejects_oversized_file(self, temp_static_dir, sample_image_bytes):
        """File exceeding size limit should be rejected."""
        # Create a file larger than 1KB limit
        large_content = sample_image_bytes + (b"\x00" * 2000)
        file = UploadFile(
            filename="large.jpg",
            file=io.BytesIO(large_content),
        )

        with pytest.raises(FileValidationError) as exc:
            await save_uploaded_file(
                file=file,
                allowed_types=["image/jpeg"],
                max_size_mb=0.001,  # 1KB limit
            )

        assert "exceeds maximum size" in str(exc.value.detail)

    async def test_generates_uuid_filename(self, temp_static_dir, sample_image_bytes):
        """Saved files should have UUID-based names, not original."""
        file = UploadFile(
            filename="../../etc/passwd.jpg",  # Malicious name
            file=io.BytesIO(sample_image_bytes),
        )

        url = await save_uploaded_file(
            file=file,
            allowed_types=["image/jpeg"],
        )

        # Should not contain original filename
        assert "passwd" not in url
        assert "etc" not in url
        # Should be a UUID pattern
        filename = url.split("/")[-1]
        assert len(filename) > 30  # UUID is 36 chars + extension

    async def test_creates_subdirectory(self, temp_static_dir, sample_image_bytes):
        """Should create subdirectory if it doesn't exist."""
        file = UploadFile(
            filename="test.jpg",
            file=io.BytesIO(sample_image_bytes),
        )

        subdir = "new/nested/directory"
        url = await save_uploaded_file(
            file=file,
            allowed_types=["image/jpeg"],
            subdirectory=subdir,
        )

        assert f"/static/{subdir}/" in url
        assert (temp_static_dir / subdir).exists()


class TestDeleteUploadedFile:
    """Tests for delete_uploaded_file function."""

    async def test_deletes_existing_file(self, temp_static_dir, sample_image_bytes):
        """Should delete existing file and return True."""
        # First upload a file
        file = UploadFile(
            filename="test.jpg",
            file=io.BytesIO(sample_image_bytes),
        )
        url = await save_uploaded_file(
            file=file,
            allowed_types=["image/jpeg"],
        )

        # Verify it exists
        file_path = temp_static_dir / url.replace("/static/", "")
        assert file_path.exists()

        # Delete it
        result = await delete_uploaded_file(url)

        assert result is True
        assert not file_path.exists()

    async def test_returns_false_for_nonexistent(self, temp_static_dir):
        """Should return False for file that doesn't exist."""
        result = await delete_uploaded_file("/static/uploads/nonexistent.jpg")
        assert result is False

    async def test_rejects_path_traversal(self, temp_static_dir):
        """Should reject path traversal attempts."""
        with pytest.raises(FileValidationError):
            await delete_uploaded_file("/static/../../../etc/passwd")

    async def test_rejects_invalid_prefix(self, temp_static_dir):
        """Should reject paths not starting with /static/."""
        with pytest.raises(FileValidationError):
            await delete_uploaded_file("/etc/passwd")
