# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""CMS photo library (CMS_ENABLED): image processing, URLs and usage checks.

Uploads are re-encoded to WebP at a few widths. The original file is never kept,
so EXIF/GPS data and anything hidden in the upload are gone for good.
"""

import io
import os
import re
import shutil
import threading
from pathlib import Path, PureWindowsPath

import magic
from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..constants import PUBLIC_URL
from ..models.cms import CmsMediaBase, CmsPageBase
from ..schemas.cms_media import CmsMediaPublic, CmsMediaRead, CmsMediaUsage
from . import file_upload
from .logging import get_logger

logger = get_logger(__name__)

# Below the 16M client_max_body_size of the host nginx made by setup-host-proxy.sh.
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
# Decompression bomb guard: a small file can declare a huge canvas.
MAX_PIXELS = 40_000_000
WIDTHS = [480, 960, 1600, 2400]
# WebP can't encode a side longer than this.
WEBP_MAX_SIDE = 16383
WEBP_QUALITY = 80

# Decoding a big photo takes a few hundred MB: a burst of uploads must not exhaust the server's memory.
_PROCESSING = threading.Semaphore(2)

# Magic MIME type → the only Pillow decoder allowed for it.
ALLOWED_FORMATS = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}

# Same rule as STATIC_ORIGIN in nuxt.config.ts: Traefik serves ./static on the `static.` subdomain.
# Overridable for hosts where that rule doesn't hold (previews use `static-<host>`).
STATIC_ORIGIN = os.environ.get("STATIC_ORIGIN") or PUBLIC_URL.replace("://", "://static.", 1)


def media_dir(media: CmsMediaBase) -> Path:
    # Read at call time so tests can patch file_upload.STATIC_DIR.
    return file_upload.STATIC_DIR / "cms" / "media" / f"{media.id}-{media.token}"


def media_url(media: CmsMediaBase, width: int) -> str:
    return f"{STATIC_ORIGIN}/cms/media/{media.id}-{media.token}/{width}.webp"


def media_to_public(media: CmsMediaBase) -> CmsMediaPublic:
    urls = {str(w): media_url(media, w) for w in media.sizes}
    return CmsMediaPublic(
        id=media.id,
        alt=media.alt,
        width=media.width,
        height=media.height,
        focal_x=media.focal_x,
        focal_y=media.focal_y,
        urls=urls,
        src=media_url(media, max(media.sizes)) if media.sizes else "",
    )


def media_to_read(media: CmsMediaBase) -> CmsMediaRead:
    return CmsMediaRead(
        **media_to_public(media).model_dump(), original_name=media.original_name, created_at=media.created_at
    )


def safe_original_name(filename: str | None) -> str:
    """Display-only name: basename without control chars. Never used as a path."""
    name = PureWindowsPath(filename or "").name  # splits on both / and \
    name = "".join(c for c in name if c.isprintable()).strip()
    return name[:255] or "photo"


def _to_srgb(img, mode: str):
    """Convert to RGB(A), baking the ICC profile in so it can be dropped without shifting colors (phone photos are often Display P3)."""
    from PIL import ImageCms

    icc = img.info.get("icc_profile")
    if icc:
        try:
            srgb = ImageCms.createProfile("sRGB")
            return ImageCms.profileToProfile(img, ImageCms.ImageCmsProfile(io.BytesIO(icc)), srgb, outputMode=mode)
        except (ImageCms.PyCMSError, OSError, ValueError):
            pass  # Broken or unsupported profile: plain conversion is good enough.
    return img.convert(mode)


def process_image(content: bytes) -> tuple[int, int, dict[int, bytes]]:
    """Validate an upload and encode it as WebP widths.

    Returns (width, height, {width: webp_bytes}) of the upright image. Raises
    HTTPException: 413 too big, 415 wrong type, 422 too many pixels, 400 unreadable.
    """
    # Imported here so apps with CMS off never load Pillow (controllers are imported either way).
    from PIL import Image, ImageOps

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB")

    mime = magic.from_buffer(content[:4096], mime=True)
    pil_format = ALLOWED_FORMATS.get(mime)
    if not pil_format:
        raise HTTPException(status_code=415, detail=f"Unsupported file type '{mime}'. Use JPEG, PNG or WebP")

    with _PROCESSING:
        try:
            # Only the header is read here, so the pixel check runs before any decoding.
            img = Image.open(io.BytesIO(content), formats=[pil_format])
            if img.width * img.height > MAX_PIXELS:
                raise HTTPException(status_code=422, detail=f"Image exceeds {MAX_PIXELS // 1_000_000} megapixels")
            img.seek(0)  # Animated files: first frame only.

            # Shrink to the largest output size before the costly steps. The target is computed on the
            # upright size (EXIF orientations 5-8 swap the sides) and also keeps the height encodable.
            swapped = img.getexif().get(0x0112, 1) in (5, 6, 7, 8)
            upright_w, upright_h = (img.height, img.width) if swapped else img.size
            scale = min(1, max(WIDTHS) / upright_w, WEBP_MAX_SIDE / upright_h)
            target = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
            if pil_format == "JPEG":
                img.draft(img.mode, target)  # The JPEG decoder skips detail at load: a fraction of the memory.
            img.load()
            if img.mode.startswith("I"):
                img = img.convert("I")  # Pillow can't shrink 16-bit modes by large factors.
            if img.size != target:
                if img.mode in ("1", "P"):
                    # Pillow resizes these nearest-neighbour, which turns fine detail into noise.
                    img = img.convert("RGBA" if img.has_transparency_data else "RGB")
                img = img.resize(target, Image.LANCZOS, reducing_gap=3.0)
            if img.mode == "I":
                # 16-bit grayscale: bring 0..65535 down to 0..255, a plain convert would clip it to white.
                img = img.point(lambda v: v / 256).convert("L")

            img = ImageOps.exif_transpose(img)
            img = _to_srgb(img, "RGBA" if img.has_transparency_data else "RGB")
            width, height = img.size
            files = {}
            for w in [w for w in WIDTHS if w <= width] or [width]:
                h = max(1, round(height * w / width))
                resized = img.resize((w, h), Image.LANCZOS, reducing_gap=3.0) if w != width else img
                buf = io.BytesIO()
                # No exif/xmp/icc passed: Pillow's WebP encoder only writes what it's given.
                resized.save(buf, "WEBP", quality=WEBP_QUALITY)
                files[w] = buf.getvalue()
        except HTTPException:
            raise
        except (OSError, SyntaxError, ValueError, Image.DecompressionBombError) as err:
            raise HTTPException(status_code=400, detail="Could not read this image") from err
    return width, height, files


def write_media_files(target: Path, files: dict[int, bytes]) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for width, data in files.items():
        (target / f"{width}.webp").write_bytes(data)


def delete_media_files(target: Path) -> None:
    shutil.rmtree(target, ignore_errors=True)
    if target.exists():
        logger.warning(f"CMS media folder still on disk after delete: {target}")


_RICHTEXT_MEDIA_RE = re.compile(r'data-media-id="(\d+)"')


def media_ids_in_fields(value) -> set[int]:
    """Media ids referenced anywhere in page fields: `{"media_id": n}` values and rich text `<img data-media-id="n">`."""
    if isinstance(value, str):
        return {int(m) for m in _RICHTEXT_MEDIA_RE.findall(value)}
    if isinstance(value, list):
        return set().union(*(media_ids_in_fields(v) for v in value))
    if isinstance(value, dict):
        ids = set().union(*(media_ids_in_fields(v) for v in value.values()))
        media_id = value.get("media_id")
        # bool is an int subclass: `True` is not a media id.
        if isinstance(media_id, int) and not isinstance(media_id, bool):
            ids.add(media_id)
        return ids
    return set()


def pages_using_media(session: Session, media_id: int) -> list[CmsMediaUsage]:
    """Pages showing this photo (cover, image field or rich text)."""
    # Scanned in Python: content sites have few pages, and this keeps the check exact (5 never matches 50).
    pages = session.query(
        CmsPageBase.id, CmsPageBase.title, CmsPageBase.fixed_key, CmsPageBase.cover_media_id, CmsPageBase.fields
    ).all()
    return [
        CmsMediaUsage(id=page_id, title=title or fixed_key or "?", fixed_key=fixed_key)
        for page_id, title, fixed_key, cover_media_id, fields in pages
        if cover_media_id == media_id or media_id in media_ids_in_fields(fields or {})
    ]
