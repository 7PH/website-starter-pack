"""
⚠️ STARTERPACK CORE — DO NOT MODIFY
HTML sanitization utilities using bleach.
"""

import bleach

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
