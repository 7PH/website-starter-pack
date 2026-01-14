# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
"""
OAuth helper for Google OAuth2 authentication.
Handles OAuth configuration, URL generation, and token exchange.
"""

import os
import secrets
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from ..constants import PUBLIC_URL

# OAuth Configuration from environment
OAUTH_ENABLED = os.environ.get("OAUTH_ENABLED", "false").lower() == "true"
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# OAuth callback URL (frontend handles the redirect)
OAUTH_CALLBACK_URL = f"{PUBLIC_URL}/oauth/callback"


@dataclass
class GoogleUserInfo:
    """User information retrieved from Google."""

    id: str  # Google's unique user ID
    email: str
    first_name: str
    last_name: str
    picture: str | None = None


def is_oauth_enabled() -> bool:
    """Check if OAuth is enabled and properly configured."""
    return OAUTH_ENABLED and bool(GOOGLE_CLIENT_ID) and bool(GOOGLE_CLIENT_SECRET)


def generate_state() -> str:
    """Generate a secure random state parameter for CSRF protection."""
    return secrets.token_urlsafe(32)


def get_google_auth_url(state: str) -> str:
    """
    Generate the Google OAuth authorization URL.

    Args:
        state: CSRF protection token to be validated on callback

    Returns:
        Full Google authorization URL with all required parameters
    """
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": OAUTH_CALLBACK_URL,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str) -> dict:
    """
    Exchange the authorization code for access tokens.

    Args:
        code: The authorization code from Google callback

    Returns:
        Token response containing access_token, id_token, etc.

    Raises:
        httpx.HTTPStatusError: If the token exchange fails
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": OAUTH_CALLBACK_URL,
            },
        )
        response.raise_for_status()
        return response.json()


async def get_google_user_info(access_token: str) -> GoogleUserInfo:
    """
    Retrieve user information from Google using the access token.

    Args:
        access_token: Valid Google OAuth access token

    Returns:
        GoogleUserInfo with user's email and name

    Raises:
        httpx.HTTPStatusError: If the API request fails
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        data = response.json()

        # Google returns id, given_name and family_name
        # Fall back to email prefix if name not available
        google_id = data.get("id", "")
        email = data.get("email", "")
        first_name = data.get("given_name", "")
        last_name = data.get("family_name", "")

        # If no name provided, use email prefix as first name
        if not first_name and not last_name:
            first_name = email.split("@")[0] if email else "User"

        return GoogleUserInfo(
            id=google_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            picture=data.get("picture"),
        )


async def get_user_from_code(code: str) -> GoogleUserInfo:
    """
    Complete OAuth flow: exchange code and get user info.

    Args:
        code: Authorization code from Google callback

    Returns:
        GoogleUserInfo with user's details

    Raises:
        httpx.HTTPStatusError: If any API request fails
    """
    tokens = await exchange_code_for_tokens(code)
    access_token = tokens.get("access_token")
    if not access_token:
        raise ValueError("No access token in response")
    return await get_google_user_info(access_token)
