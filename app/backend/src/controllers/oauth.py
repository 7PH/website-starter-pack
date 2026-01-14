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
from ..crud.organizations import get_user_organizations
from ..crud.users import create_user, get_user_by_email, update_user
from ..helpers import stripe as stripe_helper
from ..helpers.auth import create_access_token, hash_password
from ..helpers.db import get_session
from ..helpers.oauth import (
    generate_state,
    get_google_auth_url,
    get_user_from_code,
    is_oauth_enabled,
)
from ..helpers.ratelimit import ensure_rate_limit
from ..models.user import UserBase
from ..schemas.oauth import (
    OAuthCallbackRequest,
    OAuthProvider,
    OAuthStatusResponse,
    OAuthUrlResponse,
)
from ..schemas.organization import UserOrganizationInfo
from ..schemas.user import UserRead, UserTokenUpdate

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

    # Rate limit by IP
    client_ip = request.client.host if request.client else "unknown"
    ensure_rate_limit(
        action="oauth-callback",
        quota=OAUTH_CALLBACK_RATE_LIMIT,
        key=client_ip,
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

        # Create Stripe customer for new user
        if stripe_helper.is_enabled():
            user.stripe_id = stripe_helper.sync_customer(
                user_id=user.id,
                email=user.email,
                name=f"{user.first_name} {user.last_name}",
                check_user_exists=lambda uid: True,  # User was just created
            )
            stripe_helper.create_subscription(user.stripe_id)
            update_user(session, user)

        log_event(
            session,
            action=EventType.USER_REGISTER,
            user_id=user.id,
            request=request,
            details={"method": "oauth", "provider": "google"},
        )

    # Build user read with organizations
    user_read = _build_user_read_with_orgs(session, user)

    # Create and return JWT token
    return create_access_token(user_read)


def _build_user_read_with_orgs(session: Session, user: UserBase) -> UserRead:
    """Build a UserRead object with organization memberships."""
    from ..constants import ORGANIZATIONS_ENABLED

    organizations: list[UserOrganizationInfo] = []
    if ORGANIZATIONS_ENABLED:
        memberships = get_user_organizations(session, user.id)
        organizations = [
            UserOrganizationInfo(
                organization_id=m.organization_id,
                organization_name=m.organization.name if m.organization else "Unknown",
                is_admin=m.is_admin,
                has_premium_seat=m.has_premium_seat,
            )
            for m in memberships
            if m.organization and not m.organization.deleted_at
        ]
    return UserRead(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_admin=user.is_admin,
        is_premium=user.is_premium,
        has_personal_subscription=user.has_personal_subscription,
        organizations=organizations,
    )
