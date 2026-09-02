# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
"""
Security headers middleware for FastAPI.

Adds common security headers to all responses. Projects can customize
headers by creating security_headers_ext.py in the same directory.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..constants import USE_TLS
from .security_headers_ext import SECURITY_HEADERS_OVERRIDE

# Default security headers
DEFAULT_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    # HTTPS only: on a plain-HTTP host this would pin the browser to a scheme the stack doesn't serve. Terminating TLS upstream? Set USE_TLS=true.
    **({"Strict-Transport-Security": "max-age=31536000; includeSubDomains"} if USE_TLS else {}),
}

# API responses never need to load anything.
API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"


def _is_docs_path(request: Request) -> bool:
    """Swagger and ReDoc pull their assets from a CDN, so API_CSP would blank them out."""
    # url.path carries the root_path (/api) that uvicorn is mounted under.
    path = request.url.path.removeprefix(request.scope.get("root_path", ""))
    app = request.app
    return path in {p for p in (app.docs_url, app.redoc_url, app.openapi_url) if p}


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

        if "Content-Security-Policy" not in response.headers and not _is_docs_path(request):
            response.headers["Content-Security-Policy"] = API_CSP

        return response
