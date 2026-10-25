# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""CMS page logic (CMS_ENABLED): field validation and sanitizing on save, defaults and photos on read."""

import html
import re
import unicodedata
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models.cms import CmsMediaBase, CmsPageBase
from ..schemas.cms_media import CmsMediaPublic
from ..schemas.cms_page import CmsPageAdminRead, CmsPageRead, CmsPageUpdate
from .cms_media import media_ids_in_fields, media_to_public, media_to_read
from .cms_templates import Field, Template, get_templates
from .sanitize import sanitize_rich_text

SEO_DESCRIPTION_LENGTH = 155
MAX_SLUG_LENGTH = 200
# Slugs made from a title stay short; a hand-typed one may use the whole column.
AUTO_SLUG_LENGTH = 80
# Width of rich text on the public page (CmsRichText inside CmsPageContent).
RICH_TEXT_IMAGE_SIZES = "(min-width: 768px) 736px, 100vw"
# Checked before sanitizing, so absurd payloads never reach bleach.
MAX_RICH_TEXT_INPUT_LENGTH = 500_000
# Stored size and photo count of one rich text field, far above any real page.
MAX_RICH_TEXT_BYTES = 200_000
MAX_RICH_TEXT_IMAGES = 100

# 409 details, mapped to messages by the frontend.
SLUG_TAKEN = "slug_taken"
CHANGED_ELSEWHERE = "changed_elsewhere"

# Path of a generated media file: /cms/media/<id>-<token>/<width>.webp
_MEDIA_PATH = re.compile(r"/cms/media/(\d+)-([\w-]+)/\d+\.webp$")
# Stored rich text went through bleach: attribute values are always double-quoted, but may hold a raw ">".
_IMG_TAG = re.compile(r'<img\b(?:[^">]|"[^"]*")*>')
_ATTRIBUTE = re.compile(r'([\w-]+)="([^"]*)"')
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
    """URL-safe slug: "L’été à Paris" -> "l-ete-a-paris"."""
    # NFKD has no decomposition for these, they would vanish.
    value = value.lower().replace("œ", "oe").replace("æ", "ae").replace("ß", "ss")
    # Apostrophes separate words, else the typographic ones vanish too: "S’ancrer" would give "sancrer".
    value = re.sub(r"[’‘ʼ´`']", " ", value)
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
    """Accepts only images of our library (id and token must match), stamped with their id for reads to render."""

    def resolve(src: str) -> dict[str, str] | None:
        match = _MEDIA_PATH.search(urlparse(src).path)
        media = match and session.get(CmsMediaBase, int(match[1]))
        if not media or media.token != match[2]:
            return None
        return {"src": media_to_public(media).src, "data-media-id": str(media.id)}

    return resolve


def _stored_html(value: Any) -> str:
    """HTML of a stored rich text value. Wrapped in a dict so it can't be mistaken for plain text saved under another field type."""
    return value.get("html", "") if isinstance(value, dict) else ""


def _text_to_html(text: str) -> str:
    """Escaped paragraphs, one per block of lines."""
    blocks = re.split(r"\n\s*\n", text.strip())
    return "".join(f"<p>{html.escape(block.strip())}</p>".replace("\n", "<br>") for block in blocks if block.strip())


def _render_images(value: str, media: dict[int, CmsMediaPublic]) -> str:
    """Rich text images as responsive tags of their current photo, dropped when the photo is gone."""

    def render(match: re.Match) -> str:
        attributes = dict(_ATTRIBUTE.findall(match[0]))
        media_id = attributes.get("data-media-id", "")
        photo = media.get(int(media_id)) if media_id.isdigit() else None
        if not photo:
            return ""
        srcset = ", ".join(f"{url} {width}w" for width, url in photo.urls.items())
        # alt is kept as stored: bleach already escaped it.
        return (
            f'<img src="{photo.src}" srcset="{srcset}" sizes="{RICH_TEXT_IMAGE_SIZES}" alt="{attributes.get("alt", "")}"'
            f' width="{photo.width}" height="{photo.height}" loading="lazy" decoding="async" data-media-id="{photo.id}">'
        )

    return _IMG_TAG.sub(render, value)


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
        if len(value) > MAX_RICH_TEXT_INPUT_LENGTH:
            raise _invalid(f"Field '{name}' is too long")
        clean = sanitize_rich_text(value, _image_resolver(session))
        if len(clean.encode()) > MAX_RICH_TEXT_BYTES:
            raise _invalid(f"Field '{name}' is too long")
        # Sanitized: any "<img" left is a tag, text "<" is escaped.
        if clean.count("<img") > MAX_RICH_TEXT_IMAGES:
            raise _invalid(f"Field '{name}' has too many photos")
        return {"html": clean}

    value = " ".join(value.split()) if field.type == "text" else value.strip()
    if field.max is not None and len(value) > field.max:
        raise _invalid(f"Field '{name}' is longer than {field.max} characters")
    return value


def _is_empty(field: Field, value: Any) -> bool:
    if field.type == "image":
        return value is None
    if field.type == "richtext":
        return not plain_text(_stored_html(value)) and "<img" not in _stored_html(value)
    return not value


def clean_fields(session: Session, template: Template, stored: dict, values: dict) -> dict:
    """Fields to store: sent values of declared fields, validated, over stored ones.

    Stored values of fields no longer in the template are kept, so removing a field (or a whole template) loses nothing.
    Required is checked on sent fields only: a quick edit sends one field, the full editor sends them all.
    """
    fields = dict(stored)
    for name, value in values.items():
        if field := template.fields.get(name):
            fields[name] = _clean_value(session, name, field, value)
            if field.required and _is_empty(field, fields[name]):
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
            raise HTTPException(status_code=409, detail=SLUG_TAKEN)
        page.slug = slug
    if values.get("published") is not None:
        # Every (re)publication dates the page, so a post put back online sorts as new.
        if values["published"] and not page.published:
            page.published_at = datetime.now(UTC)
        page.published = values["published"]
    if values.get("published_at") is not None:
        # Sent by imports, to keep a post's original date.
        page.published_at = values["published_at"]


def _is_stale(sent: datetime | None, stored: datetime | None) -> bool:
    if sent is None or stored is None:
        return sent is not stored
    try:
        # A client that kept the date as a JS Date only has milliseconds left.
        return abs(sent - stored) >= timedelta(milliseconds=1)
    except TypeError:  # One naive, one aware.
        return True


def save_page(session: Session, page: CmsPageBase, data: CmsPageUpdate) -> None:
    """Apply an editor's changes and commit.

    409 changed_elsewhere when the page was saved since the editor loaded it (the `updated_at` sent), or a concurrent
    save created the fixed page. 409 slug_taken when another page has the address.
    """
    if "updated_at" in data.model_fields_set and _is_stale(data.updated_at, page.updated_at):
        raise HTTPException(status_code=409, detail=CHANGED_ELSEWHERE)
    apply_update(session, page, data)
    # A free page's only unique index is its slug.
    race_detail = CHANGED_ELSEWHERE if page.fixed_key is not None else SLUG_TAKEN
    session.add(page)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(status_code=409, detail=race_detail) from error
    session.refresh(page)


def new_fixed_page(key: str) -> CmsPageBase:
    """Unsaved row for a fixed page: serves its defaults until first edited."""
    return CmsPageBase(
        template=key,
        fixed_key=key,
        title="",
        fields={},
        published=False,
        seo_title="",
        seo_description="",
    )


def load_media(session: Session, pages: list[CmsPageBase], admin: bool = False) -> dict[int, CmsMediaPublic]:
    """Every photo the pages show (cover, image fields, rich text), in one query."""
    ids = set().union(*(media_ids_in_fields(p.fields or {}) for p in pages)) | {p.cover_media_id for p in pages}
    ids.discard(None)
    if not ids:
        return {}
    to_schema = media_to_read if admin else media_to_public
    return {m.id: to_schema(m) for m in session.query(CmsMediaBase).filter(CmsMediaBase.id.in_(ids))}


def _read_fields(template: Template, stored: dict, media: dict[int, CmsMediaPublic]) -> dict[str, Any]:
    """Every template field: stored value or default, photos expanded (None or dropped if gone)."""
    fields: dict[str, Any] = {}
    for name, field in template.fields.items():
        value = stored.get(name, field.default)
        if field.type == "richtext":
            if name not in stored:
                value = value or ""  # Code default: trusted.
            elif isinstance(value, str):
                value = _text_to_html(value)  # Saved while the field was plain text.
            else:
                value = _stored_html(value)
            value = _render_images(value, media)
        elif field.type == "image":
            found = media.get(value.get("media_id")) if isinstance(value, dict) else None
            value = found.model_dump(mode="json") if found else None
        elif isinstance(value, dict):
            value = plain_text(_stored_html(value))  # Saved while the field was rich text.
        fields[name] = value
    return fields


def _page_to_read(page: CmsPageBase, media: dict[int, CmsMediaPublic], admin: bool) -> CmsPageRead | CmsPageAdminRead:
    template = get_template(page.template)
    fields = _read_fields(template, page.fields or {}, media)
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
            seo_description_auto=auto_description,
        )
    return CmsPageRead(
        **common,
        seo_title=page.seo_title or page.title,
        seo_description=page.seo_description or auto_description,
    )


def pages_to_read(session: Session, pages: list[CmsPageBase], admin: bool = False) -> list[CmsPageRead]:
    """Pages with their photos, loaded in one query whatever the number of pages. Admin reads get the editor's photo shape."""
    media = load_media(session, pages, admin)
    return [_page_to_read(page, media, admin) for page in pages]


def page_to_read(session: Session, page: CmsPageBase, admin: bool = False) -> CmsPageRead | CmsPageAdminRead:
    return pages_to_read(session, [page], admin)[0]
