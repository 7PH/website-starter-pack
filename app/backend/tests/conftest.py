# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""
Pytest fixtures for backend tests.
"""

from pathlib import Path

import pytest


@pytest.fixture
def temp_static_dir(tmp_path: Path, monkeypatch):
    """
    Provides a temporary static directory for file upload tests.
    Automatically patches the STATIC_DIR in file_upload module.
    """
    static_dir = tmp_path / "static"
    static_dir.mkdir()

    # Patch the STATIC_DIR in file_upload module
    from src.helpers import file_upload

    monkeypatch.setattr(file_upload, "STATIC_DIR", static_dir)

    return static_dir


@pytest.fixture
def sample_image_bytes():
    """Minimal valid 1x1-pixel JPEG."""
    return bytes.fromhex(
        "FFD8FFE000104A46494600010100000100010000FFDB00430008060607060508"
        "0707070909080A0C140D0C0B0B0C1912130F141D1A1F1E1D1A1C1C20242E2720"
        "222C231C1C2837292C30313434341F27393D38323C2E333432FFC0000B080001"
        "000101011100FFC4001F00000105010101010101000000000000000001020304"
        "05060708090A0BFFC400B5100002010303020403050504040000017D01020300"
        "041105122131410613516107227114328191A1082342B1C11552D1F024336272"
        "82090A161718191A25262728292A3435363738393A434445464748494A535455"
        "565758595A636465666768696A737475767778797A838485868788898A929394"
        "95969798999AA2A3A4A5A6A7A8A9AAB2B3B4B5B6B7B8B9BAC2C3C4C5C6C7C8C9"
        "CAD2D3D4D5D6D7D8D9DAE1E2E3E4E5E6E7E8E9EAF1F2F3F4F5F6F7F8F9FAFFDA"
        "0008010100003F00FBD5DB20B8A3A1AD103FFFD9"
    )


@pytest.fixture
def sample_png_bytes():
    """Minimal valid 1x1-pixel PNG."""
    return bytes.fromhex(
        "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4"
        "890000000A49444154789C63000100000500010D0A2DB40000000049454E44AE"
        "426082"
    )


@pytest.fixture
def sample_text_bytes():
    """Returns plain text bytes for testing invalid uploads."""
    return b"This is just plain text, not an image."
