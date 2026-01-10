# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..constants import JWT_ACCESS_TOKEN_EXPIRE_MINUTES, ORGANIZATIONS_ENABLED, PUBLIC_URL, EventType
from ..crud.event_logs import log_event
from ..crud.organizations import get_user_organizations
from ..crud.users import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    is_email_taken,
    update_user,
)
from ..helpers import stripe as stripe_helper
from ..helpers.auth import (
    create_access_token,
    decode_access_token,
    get_current_user,
    hash_password,
    oauth2_scheme,
    verify_password,
)
from ..helpers.auth_tokens import create_email_change_token, get_email_change_url
from ..helpers.db import get_session
from ..helpers.email import send_email_change_email
from ..helpers.ratelimit import ensure_rate_limit
from ..models.user import UserBase
from ..schemas.user import (
    AuthMessageResponse,
    UserChangeEmail,
    UserChangeInfo,
    UserChangePassword,
    UserCreate,
    UserOrganizationInfo,
    UserRead,
    UserTokenUpdate,
)

router = APIRouter()

RESET_PASSWORD_BASE_URL = f"{PUBLIC_URL}/reset-password"

# Rate limit constants
LOGIN_RATE_LIMIT_PER_IP = 10  # max attempts per IP
LOGIN_RATE_LIMIT_MINUTES = 15
REGISTER_RATE_LIMIT_PER_IP = 5  # max attempts per IP
REGISTER_RATE_LIMIT_MINUTES = 15
EMAIL_CHANGE_COOLDOWN_MINUTES = 5
EMAIL_CHANGE_DAILY_LIMIT = 5
TOKEN_REFRESH_COOLDOWN_SECONDS = 300  # 5 minutes


@router.post("/users", response_model=UserTokenUpdate, status_code=status.HTTP_201_CREATED)
def register_user(*, request: Request, session: Session = Depends(get_session), user_create: UserCreate):
    # Rate limit by IP
    client_ip = request.client.host if request.client else "unknown"
    ensure_rate_limit(
        action="register",
        quota=REGISTER_RATE_LIMIT_PER_IP,
        key=client_ip,
        duration_minutes=REGISTER_RATE_LIMIT_MINUTES,
    )

    user_create.email = user_create.email.lower()
    if is_email_taken(session, user_create.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = UserBase(
        email=user_create.email,
        hashed_password=hash_password(user_create.password),
        first_name=user_create.first_name,
        last_name=user_create.last_name,
    )
    create_user(session, user)

    # Create Stripe customer and free subscription for the new user
    if stripe_helper.is_enabled():
        user.stripe_id = stripe_helper.sync_customer(
            user_id=user.id,
            email=user.email,
            name=f"{user.first_name} {user.last_name}",
            check_user_exists=lambda uid: get_user_by_id(session, uid) is not None,
        )
        stripe_helper.create_subscription(user.stripe_id)
        update_user(session, user)

    token = create_access_token(UserRead.model_validate(user))

    # Log the registration event
    log_event(session, action=EventType.USER_REGISTER, user_id=user.id, request=request)

    return UserTokenUpdate(
        access_token=token.access_token,
        token_parsed=token.token_parsed,
        user=user,
    )


@router.post("/users/login", response_model=UserTokenUpdate, status_code=status.HTTP_200_OK)
def login_user(
    *,
    request: Request,
    session: Session = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    # Rate limit by IP
    client_ip = request.client.host if request.client else "unknown"
    ensure_rate_limit(
        action="login",
        quota=LOGIN_RATE_LIMIT_PER_IP,
        key=client_ip,
        duration_minutes=LOGIN_RATE_LIMIT_MINUTES,
    )

    # Lowercase the username (email in this case) for case-insensitive login
    email = form_data.username.lower()
    password = form_data.password

    user = get_user_by_email(session, email)

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    # Log the login event
    log_event(session, action=EventType.USER_LOGIN, user_id=user.id, request=request)

    return create_access_token(_build_user_read_with_orgs(session, user))


def _build_user_read_with_orgs(session: Session, user: UserBase) -> UserRead:
    """Build a UserRead object with organization memberships (if feature enabled)."""
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


@router.get("/users/me", response_model=UserRead, status_code=status.HTTP_200_OK)
def get_me(*, session: Session = Depends(get_session), current_user: UserRead = Depends(get_current_user)):
    """
    Get the details of the currently authenticated user, including organization memberships.
    """
    user = get_user_by_id(session, current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return _build_user_read_with_orgs(session, user)


@router.put("/users/me/token", response_model=UserTokenUpdate, status_code=status.HTTP_200_OK)
def refresh_token(
    *,
    session: Session = Depends(get_session),
    token: str = Depends(oauth2_scheme),
):
    """
    Refresh the current user's token.
    Rate limited: won't issue new token if current one is less than 5 minutes old.
    """
    payload = decode_access_token(token)

    token_exp = payload.get("exp", 0)
    token_created = token_exp - (JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    now = datetime.now(UTC).timestamp()

    # Always fetch fresh user data with organizations
    user_id = payload.get("id")
    user = get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account no longer exists",
        )

    user_read = _build_user_read_with_orgs(session, user)

    if now - token_created < TOKEN_REFRESH_COOLDOWN_SECONDS:
        # Return current token info without generating new one, but with fresh user data
        return UserTokenUpdate(
            access_token=token,
            token_parsed=dict(
                user=user_read,
                created_at=datetime.fromtimestamp(token_created, tz=UTC),
                expires_at=datetime.fromtimestamp(token_exp, tz=UTC),
            ),
            user=user_read,
        )

    return create_access_token(user_read)


@router.get("/users/{user_id}", response_model=UserRead, status_code=status.HTTP_200_OK)
def get_user(
    *,
    session: Session = Depends(get_session),
    user_id: int,
    current_user: UserRead = Depends(get_current_user),
):
    """
    Get user details by ID. Only accessible by the user themselves or system admins.
    """
    # Users can only view their own details unless they're system admins
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    user = get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _build_user_read_with_orgs(session, user)


@router.patch("/users/me", response_model=UserRead, status_code=status.HTTP_200_OK)
def update_me(
    *,
    request: Request,
    session: Session = Depends(get_session),
    user_change_info: UserChangeInfo,
    current_user: UserRead = Depends(get_current_user),
):
    """
    Update the profile (name) of the currently authenticated user.
    Email changes are handled separately via POST /users/me/email-changes.
    """
    user = get_user_by_id(session, current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user_change_info.first_name is not None:
        user.first_name = user_change_info.first_name

    if user_change_info.last_name is not None:
        user.last_name = user_change_info.last_name

    update_user(session, user)

    # Sync name change to Stripe if enabled
    if stripe_helper.is_enabled() and user.stripe_id:
        stripe_helper.sync_customer(
            user_id=user.id,
            email=user.email,
            name=f"{user.first_name} {user.last_name}",
            existing_stripe_id=user.stripe_id,
        )

    # Log profile update
    log_event(session, action=EventType.USER_PROFILE_UPDATE, user_id=user.id, request=request)

    return UserRead.model_validate(user)


@router.put(
    "/users/me/password",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
)
def update_my_password(
    *,
    request: Request,
    session: Session = Depends(get_session),
    user_change_pwd: UserChangePassword,
    current_user: UserRead = Depends(get_current_user),
):
    """
    Update the password of the currently authenticated user.
    """
    user = get_user_by_id(session, current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not verify_password(user_change_pwd.old_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid current password")

    if user_change_pwd.old_password == user_change_pwd.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the old one",
        )

    user.hashed_password = hash_password(user_change_pwd.new_password)
    update_user(session, user)

    # Log password change
    log_event(session, action=EventType.USER_PASSWORD_CHANGE, user_id=user.id, request=request)

    return UserRead.model_validate(user)


@router.post(
    "/users/me/email-changes",
    response_model=AuthMessageResponse,
    status_code=status.HTTP_200_OK,
)
def request_email_change(
    *,
    request: Request,
    session: Session = Depends(get_session),
    body: UserChangeEmail,
    current_user: UserRead = Depends(get_current_user),
):
    """
    Request to change the email address of the currently authenticated user.
    Sends a confirmation email to the new address with a verification link.
    """
    user = get_user_by_id(session, current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Verify current password
    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    # Normalize and validate new email
    new_email = body.new_email.lower().strip()
    if new_email == user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="New email must be different from current email"
        )

    # Check if new email is already taken
    if is_email_taken(session, new_email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    # Rate limit: per-user cooldown
    ensure_rate_limit(
        action="email-change",
        quota=1,
        key=str(user.id),
        duration_minutes=EMAIL_CHANGE_COOLDOWN_MINUTES,
    )

    # Rate limit: per-user daily limit
    ensure_rate_limit(
        action="email-change-daily",
        quota=EMAIL_CHANGE_DAILY_LIMIT,
        key=str(user.id),
        duration_minutes=60 * 24,
    )

    # Generate token and send email to NEW address
    token = create_email_change_token(user.id, user.email, new_email)
    confirmation_url = get_email_change_url(token)

    try:  # noqa: SIM105
        send_email_change_email(
            to_email=new_email,
            username=user.first_name,
            confirmation_link=confirmation_url,
        )
    except Exception:
        # Email service might not be configured - that's OK in development
        pass

    # Log the request
    log_event(
        session,
        action=EventType.USER_PROFILE_UPDATE,
        user_id=user.id,
        request=request,
        details={"action": "email_change_requested", "new_email": new_email},
    )

    return AuthMessageResponse(message="Confirmation email sent to your new address")
