# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Pydantic schemas for CMS pages and their templates (CMS_ENABLED)."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from .cms_media import CmsMediaRead


class CmsTemplateField(BaseModel):
    name: str
    type: Literal["text", "textarea", "richtext", "image"]
    label: dict[str, str]
    help: dict[str, str]
    default: str | None
    # Title renames the generated TS type, which would clash with the global Required<T>.
    required: bool = Field(title="Is Required")
    max: int | None


class CmsTemplateRead(BaseModel):
    name: str
    label: dict[str, str]
    fixed: bool
    fields: list[CmsTemplateField]


class CmsPageRead(BaseModel):
    """A page as the public site sees it: defaults merged, photos expanded, SEO filled."""

    # None for a fixed page that was never edited (its defaults are served).
    id: int | None
    template: str
    fixed_key: str | None
    slug: str | None
    title: str
    fields: dict[str, Any]
    seo_title: str
    seo_description: str
    cover: CmsMediaRead | None
    published_at: datetime | None
    updated_at: datetime | None


class CmsPageAdminRead(CmsPageRead):
    """A page in the editor. Here seo_title and seo_description are what the editor typed, empty = automatic (title, seo_description_auto)."""

    published: bool
    show_in_blog: bool
    seo_description_auto: str


class CmsPageSummary(BaseModel):
    """A page in a list of posts: no fields, the description doubles as an excerpt."""

    id: int
    slug: str
    title: str
    seo_description: str
    cover: CmsMediaRead | None
    published_at: datetime | None


class CmsPageListResponse(BaseModel):
    items: list[CmsPageRead]
    total: int


class CmsPageOrder(BaseModel):
    """Free page ids in their new order."""

    ids: list[int] = Field(max_length=500)


class CmsPostListResponse(BaseModel):
    items: list[CmsPageSummary]
    total: int


class CmsPageCreate(BaseModel):
    template: str
    title: str = Field(min_length=1, max_length=200)


class CmsPageUpdate(BaseModel):
    """Partial update. Slug, published and show_in_blog are ignored on fixed pages."""

    title: str | None = Field(None, max_length=200)
    slug: str | None = Field(None, max_length=200)
    fields: dict[str, Any] | None = None
    published: bool | None = None
    show_in_blog: bool | None = None
    seo_title: str | None = Field(None, max_length=200)
    seo_description: str | None = Field(None, max_length=300)
    cover_media_id: int | None = None


class CmsPageListItem(BaseModel):
    id: int
    template: str
    slug: str
    title: str
    published: bool
    show_in_blog: bool
    published_at: datetime | None
    updated_at: datetime


class CmsFixedPageItem(BaseModel):
    key: str
    # None until the page is first saved.
    updated_at: datetime | None


class CmsAdminPagesResponse(BaseModel):
    fixed: list[CmsFixedPageItem]
    pages: list[CmsPageListItem]


class CmsSitemapEntry(BaseModel):
    """Shaped as a @nuxtjs/sitemap source entry so the frontend can use the endpoint as is."""

    loc: str
    lastmod: datetime
