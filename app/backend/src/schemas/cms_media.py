# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Pydantic schemas for the CMS photo library (CMS_ENABLED)."""

from datetime import datetime

from pydantic import BaseModel, Field


class CmsMediaRead(BaseModel):
    """An uploaded photo with the absolute URL of each generated width."""

    id: int
    original_name: str
    alt: str
    width: int
    height: int
    focal_x: float
    focal_y: float
    created_at: datetime
    # Keys are widths as strings, eg {"480": "https://static.../480.webp"}.
    urls: dict[str, str]
    # URL of the largest width.
    src: str


class CmsMediaListResponse(BaseModel):
    """Page of the photo library, newest first."""

    items: list[CmsMediaRead]
    total: int


class CmsMediaUsage(BaseModel):
    """A page showing a photo, listed when deleting that photo is refused (409)."""

    id: int
    title: str
    # Set for fixed pages, which are edited by key rather than id.
    fixed_key: str | None = None


class CmsMediaUpdate(BaseModel):
    """Editable fields of a photo. Omitted fields are left unchanged."""

    alt: str | None = Field(default=None, max_length=300)
    focal_x: float | None = Field(default=None, ge=0, le=1)
    focal_y: float | None = Field(default=None, ge=0, le=1)
