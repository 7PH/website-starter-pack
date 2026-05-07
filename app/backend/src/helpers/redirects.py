# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Redirect URL validation. Used by checkout/portal flows that take a return_url."""

import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def validate_redirect_url(url: str, public_url: str | None = None) -> str:
    """Validate and sanitize a redirect URL. Returns empty string if invalid.

    When ``public_url`` is set, the candidate's host must match it — this
    prevents open-redirect attacks that pivot a checkout success URL to
    an attacker-controlled domain.
    """
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return ""
        if not parsed.netloc:
            return ""
        if public_url:
            public_parsed = urlparse(public_url)
            if parsed.netloc != public_parsed.netloc:
                logger.warning(f"Redirect URL host mismatch: {parsed.netloc} != {public_parsed.netloc}")
                return ""
        return url
    except Exception:
        return ""
