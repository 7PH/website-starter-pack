"""
⚠️ STARTERPACK CORE — DO NOT MODIFY
HTML sanitization utilities using bleach.
"""

import re
from collections.abc import Callable
from functools import partial

import bleach
from bleach.html5lib_shim import Filter

# Safe tags for basic text formatting
BASIC_TAGS = [
    "p",
    "br",
    "strong",
    "b",
    "em",
    "i",
    "u",
    "ul",
    "ol",
    "li",
    "a",
    "blockquote",
    "code",
    "pre",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
]

# Tags allowed when images are enabled
IMAGE_TAGS = ["img"]

# Safe attributes per tag
BASIC_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
}

IMAGE_ATTRIBUTES = {
    "img": ["src", "alt", "title", "width", "height"],
}

# Allowed URL schemes for links
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]

# CMS rich text: what the page editor can produce, nothing more.
RICH_TEXT_TAGS = ["h2", "h3", "p", "br", "strong", "em", "a", "ul", "ol", "li", "blockquote", "img"]
RICH_TEXT_ATTRIBUTES = {"a": ["href"], "img": ["src", "alt"], "ol": ["start"]}

# Maps an <img> src to the attributes to set on it (src, srcset...), or None to drop the image.
type ImageResolver = Callable[[str], dict[str, str] | None]


def sanitize_html(html: str, allow_images: bool = False) -> str:
    """
    Sanitize HTML content using bleach.

    Removes potentially dangerous tags and attributes while preserving
    safe formatting. Prevents XSS attacks.

    Args:
        html: Raw HTML string to sanitize
        allow_images: If True, allows <img> tags with src/alt attributes

    Returns:
        Sanitized HTML string safe for rendering

    Examples:
        >>> sanitize_html("<script>alert('xss')</script>")
        ''
        >>> sanitize_html("<p>Hello <strong>world</strong></p>")
        '<p>Hello <strong>world</strong></p>'
        >>> sanitize_html('<a href="javascript:alert()">click</a>')
        '<a>click</a>'
    """
    if not html:
        return ""

    tags = BASIC_TAGS.copy()
    attributes = BASIC_ATTRIBUTES.copy()

    if allow_images:
        tags.extend(IMAGE_TAGS)
        attributes.update(IMAGE_ATTRIBUTES)

    return bleach.clean(
        html,
        tags=tags,
        attributes=attributes,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )


def strip_all_tags(html: str) -> str:
    """
    Remove all HTML tags, returning plain text.

    Args:
        html: HTML string to strip

    Returns:
        Plain text with all HTML removed
    """
    if not html:
        return ""

    return bleach.clean(html, tags=[], strip=True)


class _ImageFilter(Filter):
    """Keeps only images the resolver accepts and sets the attributes it returns."""

    def __init__(self, source, resolve_image: ImageResolver):
        super().__init__(source)
        self.resolve_image = resolve_image

    def __iter__(self):
        for token in super().__iter__():
            if token.get("name") == "img" and token["type"] in ("StartTag", "EmptyTag"):
                attributes = self.resolve_image(token["data"].get((None, "src"), ""))
                if attributes is None:
                    continue
                token["data"].update({(None, name): value for name, value in attributes.items()})
            yield token


# Stripping keeps a removed tag's text, which for these is code, not content. Bleach still cleans everything after.
_CODE_BLOCKS = re.compile(r"<(script|style)\b[^>]*>.*?(</\1\s*>|$)", re.IGNORECASE | re.DOTALL)


def sanitize_rich_text(html: str, resolve_image: ImageResolver) -> str:
    """Sanitize CMS rich text: editor tags only, safe links, images only from the media library."""
    if not html:
        return ""

    cleaner = bleach.Cleaner(
        tags=RICH_TEXT_TAGS,
        attributes=RICH_TEXT_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
        filters=[partial(_ImageFilter, resolve_image=resolve_image)],
    )
    return cleaner.clean(_CODE_BLOCKS.sub("", html))
