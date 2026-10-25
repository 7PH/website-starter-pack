# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""CMS models (CMS_ENABLED): editors, media library and pages.

Tables are created by ``create_all`` in every app, flag on or off. They stay
empty when the flag is off. Editor rights live in their own table rather than a
``users`` column so upgrading apps needs no ALTER on ``users``.
"""

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.dialects.postgresql import JSONB

from ..helpers.db import Base


class CmsEditorBase(Base):
    """A user allowed to edit CMS content (pages, media) without being admin."""

    __tablename__ = "cms_editors"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CmsMediaBase(Base):
    """An uploaded image. Files live in static/cms/media/<id>-<token>/, one WebP per width."""

    __tablename__ = "cms_media"

    id = Column(Integer, primary_key=True)
    # Random part of the folder name: photos of draft pages can't be found by trying ids.
    token = Column(String(16), nullable=False)
    original_name = Column(String(255), nullable=False)
    alt = Column(String(300), nullable=False, server_default="")
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    # Generated widths, ascending, eg [480, 960, 1600].
    sizes = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    # Point to keep in frame when cropping, 0..1 from the top-left corner.
    focal_x = Column(Float, nullable=False, server_default=text("0.5"))
    focal_y = Column(Float, nullable=False, server_default=text("0.5"))
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CmsPageBase(Base):
    """A page built from a template declared in code.

    Fixed templates have exactly one row, keyed by ``fixed_key`` with no slug.
    Free templates have any number of rows, each served at its ``slug``.
    """

    __tablename__ = "cms_pages"

    id = Column(Integer, primary_key=True)
    template = Column(String(64), nullable=False)
    fixed_key = Column(String(64), nullable=True)
    slug = Column(String(200), nullable=True)
    title = Column(String(200), nullable=False, server_default="")
    fields = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    published = Column(Boolean, nullable=False, server_default=text("false"))
    seo_title = Column(String(200), nullable=False, server_default="")
    seo_description = Column(String(300), nullable=False, server_default="")
    cover_media_id = Column(Integer, ForeignKey("cms_media.id", ondelete="SET NULL"), nullable=True)
    # Order the editor gives free pages of a same template (eg a list of services), lowest first.
    position = Column(Integer, nullable=False, server_default=text("0"))
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_cms_pages_slug", "slug", unique=True, postgresql_where=text("slug IS NOT NULL")),
        Index("idx_cms_pages_fixed_key", "fixed_key", unique=True, postgresql_where=text("fixed_key IS NOT NULL")),
    )
