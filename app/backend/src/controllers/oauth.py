# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
"""
OAuth controller for Google OAuth2 authentication.
Provides endpoints for initiating OAuth flow and handling callbacks.
"""

import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..constants import EventType
from ..crud.event_logs import log_event
from ..crud.users import create_user, get_user_by_email
from ..helpers.auth import hash_password, issue_jwt_with_orgs, setup_new_user_stripe
from ..helpers.db import get_session
from ..helpers.oauth import (
    generate_state,
    get_google_auth_url,
    get_user_from_code,
    is_oauth_enabled,
)
from ..helpers.ratelimit import ensure_rate_limit, get_client_ip
from ..models.user import UserBase
from ..schemas.oauth import (
    OAuthCallbackRequest,
    OAuthProvider,
    OAuthStatusResponse,
    OAuthUrlResponse,
)
from ..schemas.user import UserTokenUpdate

router = APIRouter(prefix="/oauth")

# Rate limit constants
OAUTH_CALLBACK_RATE_LIMIT = 10  # max attempts per IP
OAUTH_CALLBACK_RATE_LIMIT_MINUTES = 15


@router.get("/status", response_model=OAuthStatusResponse)
def get_oauth_status():
    """
    Check if OAuth is enabled and which providers are available.
    This endpoint is public and helps the frontend know whether to show OAuth buttons.
    """
    providers = []
    if is_oauth_enabled():
        providers.append("google")
    return OAuthStatusResponse(enabled=is_oauth_enabled(), providers=providers)


@router.get("/google/url", response_model=OAuthUrlResponse)
def get_google_oauth_url():
    """
    Get the Google OAuth authorization URL.
    Returns a URL and state token that the frontend should use to redirect the user.
    The state token should be saved and validated on callback.
    """
    if not is_oauth_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth is not enabled",
        )

    state = generate_state()
    url = get_google_auth_url(state)
    return OAuthUrlResponse(url=url, state=state)


@router.post("/google/callback", response_model=UserTokenUpdate)
async def handle_google_callback(
    *,
    request: Request,
    session: Session = Depends(get_session),
    body: OAuthCallbackRequest,
):
    """
    Handle the Google OAuth callback.
    Exchanges the authorization code for user info and creates/links user account.

    - If user with email exists: logs them in (auto-link)
    - If user doesn't exist: creates new account

    Returns JWT token for authentication.
    """
    if not is_oauth_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth is not enabled",
        )

    ensure_rate_limit(
        action="oauth-callback",
        quota=OAUTH_CALLBACK_RATE_LIMIT,
        key=get_client_ip(request),
        duration_minutes=OAUTH_CALLBACK_RATE_LIMIT_MINUTES,
    )

    try:
        # Exchange code for user info from Google
        google_user = await get_user_from_code(body.code)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to authenticate with Google. Please try again.",
        ) from e

    if not google_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not retrieve email from Google account",
        )

    email = google_user.email.lower()

    # Check if user already exists (auto-link by email)
    user = get_user_by_email(session, email)

    if user:
        # Only link to an account that already proved this address.
        if not user.email_confirmed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An unverified account already uses this email. Confirm it first, then sign in with Google.",
            )
        # Existing user - log them in
        log_event(
            session,
            action=EventType.USER_LOGIN,
            user_id=user.id,
            request=request,
            details={"method": "oauth", "provider": "google"},
        )
    else:
        # New user - create account
        # Generate a random password (user won't use it, but field is required)
        random_password = secrets.token_urlsafe(32)

        user = UserBase(
            email=email,
            hashed_password=hash_password(random_password),
            first_name=google_user.first_name,
            last_name=google_user.last_name.upper() if google_user.last_name else "",
            email_confirmed=True,  # Google emails are pre-verified
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id=google_user.id,
        )
        create_user(session, user)

        setup_new_user_stripe(session, user, allow_orphan_reuse=False)

        log_event(
            session,
            action=EventType.USER_REGISTER,
            user_id=user.id,
            request=request,
            details={"method": "oauth", "provider": "google"},
        )

    return issue_jwt_with_orgs(session, user)
