# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""CMS page logic (CMS_ENABLED): field validation on save, defaults and photos on read."""

import html
import re
import unicodedata
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models.cms import CmsMediaBase, CmsPageBase
from ..schemas.cms_media import CmsMediaRead
from ..schemas.cms_page import CmsPageAdminRead, CmsPageRead, CmsPageSummary, CmsPageUpdate
from .cms_media import media_to_read
from .cms_templates import Field, Template, get_templates
from .sanitize import sanitize_rich_text

SEO_DESCRIPTION_LENGTH = 155
MAX_SLUG_LENGTH = 200
# Slugs made from a title stay short; a hand-typed one may use the whole column.
AUTO_SLUG_LENGTH = 80
# Width of rich text on the public page (CmsRichText inside CmsPageContent).
RICH_TEXT_IMAGE_SIZES = "(min-width: 768px) 736px, 100vw"
# Far above any real page, only stops absurd payloads.
MAX_RICH_TEXT_LENGTH = 500_000

# Path of a generated media file: /cms/media/<id>/<width>.webp
_MEDIA_PATH = re.compile(r"/cms/media/(\d+)/(\d+)\.webp$")
_BLOCK_END = re.compile(r"</(?:p|h2|h3|li|blockquote)>|<br\s*/?>")
_TAG = re.compile(r"<[^>]+>")

# Addresses a page can't take: it would be hidden by the site or blocked by robots.txt.
# - prefixes: Traefik sends /api* to the backend, robots.txt disallows /api* and /admin*
# - exact: core top-level routes. sitemap.xml, robots.txt, _nuxt and __sitemap__ need no entry: slugify drops dots and underscores.
RESERVED_SLUG_PREFIXES = ("api", "admin")
RESERVED_SLUGS = {
    "account",
    "c",
    "confirm-email-change",
    "delete-account",
    "invitations",
    "legal",
    "login",
    "managed-account-groups",
    "messages",
    "oauth",
    "organizations",
    "premium",
    "reset-password",
    "verify-email",
}

# Rows whose template was removed from the code keep their stored fields, unused until it comes back.
_UNKNOWN_TEMPLATE = Template(label={}, fields={})


def get_template(name: str) -> Template:
    return get_templates().get(name, _UNKNOWN_TEMPLATE)


def slugify(value: str) -> str:
    """URL-safe slug: "L'été à Paris" -> "l-ete-a-paris"."""
    # NFKD has no decomposition for these, they would vanish.
    value = value.lower().replace("œ", "oe").replace("æ", "ae").replace("ß", "ss")
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", value)[:MAX_SLUG_LENGTH].strip("-")


def is_reserved_slug(slug: str) -> bool:
    return slug in RESERVED_SLUGS or slug.startswith(RESERVED_SLUG_PREFIXES)


def auto_slug(title: str) -> str:
    """Slug for a title: at most AUTO_SLUG_LENGTH, cut between words, moved off reserved addresses."""
    slug = slugify(title) or "page"
    if len(slug) > AUTO_SLUG_LENGTH:
        cut = slug[: AUTO_SLUG_LENGTH + 1]
        slug = cut.rsplit("-", 1)[0] if "-" in cut else slug[:AUTO_SLUG_LENGTH]
    return f"page-{slug}" if is_reserved_slug(slug) else slug


def unique_slug(session: Session, title: str) -> str:
    base = auto_slug(title)
    # A prefix every candidate shares, even the ones truncated to fit their suffix.
    prefix = base[: MAX_SLUG_LENGTH - 10]
    taken = {s for (s,) in session.query(CmsPageBase.slug).filter(CmsPageBase.slug.like(f"{prefix}%"))}
    slug, n = base, 2
    while slug in taken:
        suffix = f"-{n}"
        slug, n = f"{base[: MAX_SLUG_LENGTH - len(suffix)]}{suffix}", n + 1
    return slug


def plain_text(value: Any) -> str:
    """Plain text of a field value (HTML or text), whitespace collapsed."""
    if not isinstance(value, str):
        return ""
    text = html.unescape(_TAG.sub("", _BLOCK_END.sub(" ", value)))
    return " ".join(text.split())


def _truncate(text: str, length: int) -> str:
    if len(text) <= length:
        return text
    return text[:length].rsplit(" ", 1)[0] + "…"


def auto_seo_description(template: Template, fields: dict[str, Any]) -> str:
    """Start of the first rich text, else textarea, else text field that has content."""
    for field_type in ("richtext", "textarea", "text"):
        for name, field in template.fields.items():
            if field.type == field_type and (text := plain_text(fields.get(name, field.default))):
                return _truncate(text, SEO_DESCRIPTION_LENGTH)
    return ""


def _invalid(message: str) -> HTTPException:
    return HTTPException(status_code=422, detail=message)


def _media_exists(session: Session, media_id: Any) -> bool:
    return type(media_id) is int and session.get(CmsMediaBase, media_id) is not None


def _image_resolver(session: Session):
    """Accepts only images of our library, rewritten to their canonical URL."""

    def resolve(src: str) -> dict[str, str] | None:
        match = _MEDIA_PATH.search(urlparse(src).path)
        media = match and session.get(CmsMediaBase, int(match[1]))
        if not media:
            return None
        read = media_to_read(media)
        return {
            "src": read.urls.get(match[2], read.src),
            "srcset": ", ".join(f"{url} {width}w" for width, url in read.urls.items()),
            "sizes": RICH_TEXT_IMAGE_SIZES,
            "width": str(read.width),
            "height": str(read.height),
            "loading": "lazy",
            "decoding": "async",
            "data-media-id": str(media.id),
        }

    return resolve


def _clean_value(session: Session, name: str, field: Field, value: Any) -> Any:
    if field.type == "image":
        if value is None:
            return None
        media_id = value.get("media_id") if isinstance(value, dict) else None
        if not _media_exists(session, media_id):
            raise _invalid(f"Field '{name}': unknown photo")
        return {"media_id": media_id}

    if not isinstance(value, str):
        raise _invalid(f"Field '{name}' must be text")
    if field.type == "richtext":
        if len(value) > MAX_RICH_TEXT_LENGTH:
            raise _invalid(f"Field '{name}' is too long")
        return sanitize_rich_text(value, _image_resolver(session))

    value = " ".join(value.split()) if field.type == "text" else value.strip()
    if field.max is not None and len(value) > field.max:
        raise _invalid(f"Field '{name}' is longer than {field.max} characters")
    return value


def _is_empty(field: Field, value: Any) -> bool:
    if field.type == "image":
        return value is None
    if field.type == "richtext":
        return not plain_text(value) and "<img" not in (value or "")
    return not value


def clean_fields(session: Session, template: Template, stored: dict, values: dict) -> dict:
    """Fields to store: sent values of declared fields, validated, over stored ones.

    Stored values of fields no longer in the template are kept, so removing a field (or a whole template) loses nothing.
    """
    fields = dict(stored)
    for name, value in values.items():
        if field := template.fields.get(name):
            fields[name] = _clean_value(session, name, field, value)
    for name, field in template.fields.items():
        if field.required and _is_empty(field, fields.get(name, field.default)):
            raise _invalid(f"Field '{name}' is required")
    return fields


def apply_update(session: Session, page: CmsPageBase, data: CmsPageUpdate) -> None:
    """Validate and apply an editor's changes to a page (not committed)."""
    values = data.model_dump(exclude_unset=True)
    template = get_template(page.template)

    if "fields" in values:
        page.fields = clean_fields(session, template, page.fields or {}, values["fields"] or {})
    for key in ("title", "seo_title", "seo_description"):
        if values.get(key) is not None:
            setattr(page, key, " ".join(values[key].split()))
    if "cover_media_id" in values:
        if values["cover_media_id"] is not None and not _media_exists(session, values["cover_media_id"]):
            raise _invalid("Unknown cover photo")
        page.cover_media_id = values["cover_media_id"]

    if page.fixed_key is not None:
        return
    if not page.title:
        raise _invalid("Title is required")
    if values.get("slug") is not None:
        slug = slugify(values["slug"])
        if not slug:
            raise _invalid("Address is required")
        if is_reserved_slug(slug):
            raise _invalid("This address is reserved by the site")
        clash = session.query(CmsPageBase.id).filter(CmsPageBase.slug == slug, CmsPageBase.id != page.id).first()
        if clash:
            raise HTTPException(status_code=409, detail="Another page already uses this address")
        page.slug = slug
    if values.get("show_in_blog") is not None:
        page.show_in_blog = values["show_in_blog"]
    if values.get("published") is not None:
        # Every (re)publication dates the page, so a post put back online sorts as new.
        if values["published"] and not page.published:
            page.published_at = datetime.now(UTC)
        page.published = values["published"]


def save_page(session: Session, page: CmsPageBase, data: CmsPageUpdate) -> None:
    """Apply an editor's changes and commit. 409 when a concurrent save took the slug or created the fixed page."""
    apply_update(session, page, data)
    session.add(page)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(status_code=409, detail="This page or its address was just saved elsewhere") from error
    session.refresh(page)


def new_fixed_page(key: str) -> CmsPageBase:
    """Unsaved row for a fixed page: serves its defaults until first edited."""
    return CmsPageBase(
        template=key,
        fixed_key=key,
        title="",
        fields={},
        published=False,
        show_in_blog=False,
        seo_title="",
        seo_description="",
    )


def _media_map(session: Session, ids: set[int]) -> dict[int, CmsMediaRead]:
    if not ids:
        return {}
    rows = session.query(CmsMediaBase).filter(CmsMediaBase.id.in_(ids)).all()
    return {m.id: media_to_read(m) for m in rows}


def _image_ids(template: Template, fields: dict) -> set[int]:
    return {
        value["media_id"]
        for name, field in template.fields.items()
        if field.type == "image" and isinstance(value := fields.get(name), dict) and "media_id" in value
    }


def _read_fields(session: Session, template: Template, stored: dict, media: dict[int, CmsMediaRead]) -> dict[str, Any]:
    """Every template field: stored value or default, photos expanded (None if gone)."""
    fields: dict[str, Any] = {}
    for name, field in template.fields.items():
        value = stored.get(name, field.default)
        if field.type == "richtext":
            # Also on read: the field may have held plain text (raw HTML included) before its type changed.
            value = sanitize_rich_text(value, _image_resolver(session)) if isinstance(value, str) else ""
        elif field.type == "image":
            found = media.get(value["media_id"]) if isinstance(value, dict) else None
            value = found.model_dump(mode="json") if found else None
        fields[name] = value
    return fields


def page_to_read(session: Session, page: CmsPageBase, admin: bool = False) -> CmsPageRead | CmsPageAdminRead:
    template = get_template(page.template)
    stored = page.fields or {}
    media = _media_map(session, _image_ids(template, stored) | ({page.cover_media_id} - {None}))
    fields = _read_fields(session, template, stored, media)
    auto_description = auto_seo_description(template, fields)
    common = dict(
        id=page.id,
        template=page.template,
        fixed_key=page.fixed_key,
        slug=page.slug,
        title=page.title,
        fields=fields,
        cover=media.get(page.cover_media_id),
        published_at=page.published_at,
        updated_at=page.updated_at,
    )
    if admin:
        return CmsPageAdminRead(
            **common,
            seo_title=page.seo_title,
            seo_description=page.seo_description,
            published=page.published,
            show_in_blog=page.show_in_blog,
            seo_description_auto=auto_description,
        )
    return CmsPageRead(
        **common,
        seo_title=page.seo_title or page.title,
        seo_description=page.seo_description or auto_description,
    )


def pages_to_summaries(session: Session, pages: list[CmsPageBase]) -> list[CmsPageSummary]:
    media = _media_map(session, {p.cover_media_id for p in pages} - {None})
    return [
        CmsPageSummary(
            id=p.id,
            slug=p.slug,
            title=p.title,
            seo_description=p.seo_description or auto_seo_description(get_template(p.template), p.fields or {}),
            cover=media.get(p.cover_media_id),
            published_at=p.published_at,
        )
        for p in pages
    ]
