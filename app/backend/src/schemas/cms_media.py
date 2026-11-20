# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Pydantic schemas for the CMS photo library (CMS_ENABLED)."""

from datetime import datetime

from pydantic import BaseModel, Field


class CmsMediaPublic(BaseModel):
    """A photo as public pages show it, with the absolute URL of each generated width."""

    id: int
    alt: str
    width: int
    height: int
    focal_x: float
    focal_y: float
    # Keys are widths as strings, eg {"480": "https://static.../480.webp"}.
    urls: dict[str, str]
    # URL of the largest width.
    src: str


class CmsMediaRead(CmsMediaPublic):
    """A photo in the library, as editors see it."""

    original_name: str
    folder: str | None = None
    created_at: datetime


class CmsMediaUsage(BaseModel):
    """A page showing a photo (cover, image field or rich text), published or not."""

    id: int
    title: str
    # Set for fixed pages, which are edited by key rather than id.
    fixed_key: str | None = None


class CmsMediaLibraryItem(CmsMediaRead):
    """A photo in a library listing, with the number of pages showing it."""

    usage_count: int


class CmsMediaDetail(CmsMediaRead):
    """One photo with the pages showing it."""

    used_by: list[CmsMediaUsage]


class CmsMediaListResponse(BaseModel):
    """Page of the photo library for the given filters."""

    items: list[CmsMediaLibraryItem]
    total: int
    # Photos shown on a page but without a description, whatever the filters.
    missing_alt: int
    # Every folder in use, sorted.
    folders: list[str]


class CmsMediaUpdate(BaseModel):
    """Editable fields of a photo. Omitted fields are left unchanged."""

    alt: str | None = Field(default=None, max_length=300)
    focal_x: float | None = Field(default=None, ge=0, le=1)
    focal_y: float | None = Field(default=None, ge=0, le=1)
    # "" takes the photo out of its folder.
    folder: str | None = Field(default=None, max_length=100)


class CmsMediaBulkDelete(BaseModel):
    ids: list[int] = Field(min_length=1, max_length=2000)


class CmsMediaBulkDeleteResponse(BaseModel):
    deleted: list[int]
    # Shown on a page, so left alone.
    in_use: list[int]


class CmsMediaBulkUpdate(BaseModel):
    ids: list[int] = Field(min_length=1, max_length=2000)
    # "" takes the photos out of their folder.
    folder: str = Field(max_length=100)
