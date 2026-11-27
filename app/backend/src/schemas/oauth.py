# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
"""OAuth-related Pydantic schemas for API requests/responses."""

from enum import StrEnum

from pydantic import BaseModel

from .user import UserTokenUpdate


class OAuthProvider(StrEnum):
    """Supported OAuth providers."""

    GOOGLE = "google"
    # Future providers: GITHUB = "github", MICROSOFT = "microsoft"


class OAuthUrlResponse(BaseModel):
    """Response containing the OAuth authorization URL."""

    url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    """Request body for OAuth callback."""

    code: str
    state: str


class OAuthStatusResponse(BaseModel):
    """Response indicating OAuth availability."""

    enabled: bool
    providers: list[str]


class OAuthCallbackResponse(UserTokenUpdate):
    """Token for the signed-in user. ``is_new_user`` tells a sign-up from a sign-in, eg for analytics."""

    is_new_user: bool = False
