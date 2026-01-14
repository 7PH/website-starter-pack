# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
"""
Security headers middleware for FastAPI.

Adds common security headers to all responses. Projects can customize
headers by creating security_headers_ext.py in the same directory.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .security_headers_ext import SECURITY_HEADERS_OVERRIDE

# Default security headers
DEFAULT_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}


# Merge defaults with overrides (overrides win, empty string removes header)
SECURITY_HEADERS = {**DEFAULT_SECURITY_HEADERS, **SECURITY_HEADERS_OVERRIDE}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.

    To customize headers, create `security_headers_ext.py` in the helpers directory:

        # app/backend/src/helpers/security_headers_ext.py
        SECURITY_HEADERS_OVERRIDE = {
            "X-Frame-Options": "",  # Empty string removes the header
            "X-Custom-Header": "value",  # Add new headers
        }

    To skip headers for specific routes, check request.url.path in your
    own middleware and set response headers accordingly.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Add security headers to response
        for header, value in SECURITY_HEADERS.items():
            if value:  # Only add if value is non-empty
                response.headers[header] = value

        return response
