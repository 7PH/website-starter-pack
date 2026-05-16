# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Trusted-proxy real-client-IP resolution.

Behind Traefik / Cloudflare / nginx, `request.client.host` is the proxy, not the
end user. Rate limits keyed off that collapse into one bucket and event logs
become useless. This middleware reads a header set by a trusted ingress and
stamps the result on `request.state.real_ip`.

Trust model: opt-in. `TRUSTED_IP_HEADER` defaults to empty. When empty, we
just use `request.client.host` and the middleware is a no-op. Only set
`TRUSTED_IP_HEADER` when something in front of the backend (Traefik, an LB) is
the only ingress route; if a client can reach the backend directly with that
header set, they can spoof their IP.

We take the RIGHTMOST entry of the header, not the leftmost. The convention is
"each proxy appends the IP it observed", so the rightmost entry is what our
direct proxy saw (i.e. the real client when there's one trusted hop in front).
Taking leftmost would be spoofable: Traefik's default behavior is to APPEND to
existing X-Forwarded-For, so a client-supplied leading entry would win.

Multi-hop ingress (e.g. CDN -> Traefik -> backend) returns the CDN's IP, not
the user. If you need to peel multiple layers, extend this helper rather than
making every caller do header parsing.
"""

import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


def _resolve_real_ip(request: Request) -> str:
    header_name = os.environ.get("TRUSTED_IP_HEADER", "").strip()
    if header_name:
        raw = request.headers.get(header_name)
        if raw:
            parts = [p.strip() for p in raw.split(",") if p.strip()]
            if parts:
                return parts[-1]
    if request.client:
        return request.client.host
    return "unknown"


class RealIPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.real_ip = _resolve_real_ip(request)
        return await call_next(request)


def get_real_ip(request: Request) -> str:
    """Read the cached real-IP, falling back to live resolution.

    Use this from request handlers / CRUD helpers instead of touching headers
    or `request.client` directly, so a single env knob controls trust policy.
    """
    real_ip = getattr(request.state, "real_ip", None)
    if real_ip:
        return real_ip
    return _resolve_real_ip(request)
