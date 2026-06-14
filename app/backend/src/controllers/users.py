# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..constants import JWT_ACCESS_TOKEN_EXPIRE_MINUTES, PUBLIC_URL, EventType
from ..crud.event_logs import log_event
from ..crud.users import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    is_email_taken,
    update_user,
)
from ..helpers.auth import (
    build_user_read_with_orgs,
    create_access_token,
    decode_access_token,
    get_current_nonmanaged_user,
    get_current_user,
    get_user_or_404,
    hash_password,
    issue_jwt_with_orgs,
    oauth2_scheme,
    setup_new_user_stripe,
    sync_existing_user_to_stripe,
    verify_password,
)
from ..helpers.auth_app import pre_login
from ..helpers.auth_tokens import (
    create_account_deletion_token,
    create_email_change_token,
    get_account_deletion_url,
    get_email_change_url,
)
from ..helpers.db import get_session
from ..helpers.email import (
    send_account_deletion_email,
    send_email_change_email,
    swallow_email_errors,
)
from ..helpers.ratelimit import ensure_rate_limit, ensure_user_cooldown_and_daily, get_client_ip
from ..models.user import UserBase
from ..schemas.user import (
    AuthMessageResponse,
    UserChangeEmail,
    UserChangeInfo,
    UserChangePassword,
    UserCreate,
    UserRead,
    UserTokenUpdate,
)
from ..schemas.user_ext import UserCustomData

router = APIRouter()
logger = logging.getLogger(__name__)

RESET_PASSWORD_BASE_URL = f"{PUBLIC_URL}/reset-password"

# Rate limit constants
LOGIN_RATE_LIMIT_PER_IP = 10  # max attempts per IP
LOGIN_RATE_LIMIT_MINUTES = 15
REGISTER_RATE_LIMIT_PER_IP = 5  # max attempts per IP
REGISTER_RATE_LIMIT_MINUTES = 15
EMAIL_CHANGE_COOLDOWN_MINUTES = 5
EMAIL_CHANGE_DAILY_LIMIT = 5
ACCOUNT_DELETION_COOLDOWN_MINUTES = 5
ACCOUNT_DELETION_DAILY_LIMIT = 5
TOKEN_REFRESH_COOLDOWN_SECONDS = 300  # 5 minutes


@router.post("/users", response_model=UserTokenUpdate, status_code=status.HTTP_201_CREATED)
def register_user(*, request: Request, session: Session = Depends(get_session), user_create: UserCreate):
    ensure_rate_limit(
        action="register",
        quota=REGISTER_RATE_LIMIT_PER_IP,
        key=get_client_ip(request),
        duration_minutes=REGISTER_RATE_LIMIT_MINUTES,
    )

    user_create.email = user_create.email.lower()
    # This 409 lets a caller tell taken emails from free ones (account
    # enumeration). Accepted tradeoff: a signup form must tell the user the
    # email is taken so they can log in instead, so it can't return a uniform
    # response the way password-reset does. The per-IP register rate limit above
    # throttles bulk enumeration. Apps wanting zero enumeration need a
    # verification-first signup flow (always 2xx, "you already have an account"
    # email) — a larger change, intentionally not done here.
    if is_email_taken(session, user_create.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    custom_data: dict = {}
    if user_create.custom_data is not None:
        custom_data = user_create.custom_data.model_dump(exclude_none=True)

    user = UserBase(
        email=user_create.email,
        hashed_password=hash_password(user_create.password),
        first_name=user_create.first_name,
        last_name=user_create.last_name,
        custom_data=custom_data,
    )
    create_user(session, user)

    setup_new_user_stripe(session, user)

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
    ensure_rate_limit(
        action="login",
        quota=LOGIN_RATE_LIMIT_PER_IP,
        key=get_client_ip(request),
        duration_minutes=LOGIN_RATE_LIMIT_MINUTES,
    )

    # Lowercase the username (email in this case) for case-insensitive login
    email = form_data.username.lower()
    password = form_data.password

    user = get_user_by_email(session, email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    hook = pre_login(session, user, password)
    if hook is False or (hook is None and not verify_password(password, user.hashed_password)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    # Log the login event
    log_event(session, action=EventType.USER_LOGIN, user_id=user.id, request=request)

    return issue_jwt_with_orgs(session, user)


@router.get("/users/me", response_model=UserRead, status_code=status.HTTP_200_OK)
def get_me(*, session: Session = Depends(get_session), current_user: UserRead = Depends(get_current_user)):
    """
    Get the details of the currently authenticated user, including organization memberships.
    """
    user = get_user_or_404(session, current_user.id)

    return build_user_read_with_orgs(session, user)


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

    user_read = build_user_read_with_orgs(session, user)

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

    user = get_user_or_404(session, user_id)
    return build_user_read_with_orgs(session, user)


@router.patch("/users/me", response_model=UserRead, status_code=status.HTTP_200_OK)
def update_me(
    *,
    request: Request,
    session: Session = Depends(get_session),
    user_change_info: UserChangeInfo,
    # Block managed accounts: their owner manages naming via /me/managed-accounts/:id.
    current_user: UserRead = Depends(get_current_nonmanaged_user),
):
    """
    Update the profile (name) of the currently authenticated user.
    Email changes are handled separately via POST /users/me/email-changes.
    """
    user = get_user_or_404(session, current_user.id)

    if user_change_info.first_name is not None:
        user.first_name = user_change_info.first_name

    if user_change_info.last_name is not None:
        user.last_name = user_change_info.last_name

    if user_change_info.custom_data is not None:
        incoming = user_change_info.custom_data.model_dump(exclude_none=True)
        merged = {**(user.custom_data or {}), **incoming}
        # mode="json" so stored ISO-string datetimes (e.g. last_seen_at) stay
        # JSON-serializable for the JSONB write instead of becoming datetime objects.
        user.custom_data = UserCustomData(**merged).model_dump(mode="json", exclude_none=True)

    update_user(session, user)

    sync_existing_user_to_stripe(user)

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
    # Managed accounts have no password to change.
    current_user: UserRead = Depends(get_current_nonmanaged_user),
):
    """
    Update the password of the currently authenticated user.
    """
    user = get_user_or_404(session, current_user.id)

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
    # Managed accounts have no email; nothing to change.
    current_user: UserRead = Depends(get_current_nonmanaged_user),
):
    """
    Request to change the email address of the currently authenticated user.
    Sends a confirmation email to the new address with a verification link.
    """
    user = get_user_or_404(session, current_user.id)

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

    ensure_user_cooldown_and_daily(
        action="email-change",
        user_id=user.id,
        cooldown_minutes=EMAIL_CHANGE_COOLDOWN_MINUTES,
        daily_quota=EMAIL_CHANGE_DAILY_LIMIT,
    )

    # Generate token and send email to NEW address
    token = create_email_change_token(user.id, user.email, new_email)
    confirmation_url = get_email_change_url(token)

    with swallow_email_errors():
        send_email_change_email(
            to_email=new_email,
            username=user.first_name,
            confirmation_link=confirmation_url,
        )

    # Log the request
    log_event(
        session,
        action=EventType.USER_PROFILE_UPDATE,
        user_id=user.id,
        request=request,
        details={"action": "email_change_requested", "new_email": new_email},
    )

    return AuthMessageResponse(message="Confirmation email sent to your new address")


@router.post(
    "/users/me/account-deletions",
    response_model=AuthMessageResponse,
    status_code=status.HTTP_200_OK,
)
def request_account_deletion(
    *,
    request: Request,
    session: Session = Depends(get_session),
    # Only the group owner can delete a managed account (via /me/managed-accounts/:id).
    current_user: UserRead = Depends(get_current_nonmanaged_user),
):
    """
    Request deletion of the current user's account.
    Sends a confirmation email with a link that expires in 1 hour.
    """
    user = get_user_or_404(session, current_user.id)

    if not user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send deletion email: no email address on file",
        )

    ensure_user_cooldown_and_daily(
        action="account-deletion-request",
        user_id=user.id,
        cooldown_minutes=ACCOUNT_DELETION_COOLDOWN_MINUTES,
        daily_quota=ACCOUNT_DELETION_DAILY_LIMIT,
    )

    token = create_account_deletion_token(user.id, user.email)
    confirmation_url = get_account_deletion_url(token)

    # Surface email-send failures: if the user can't get the link, they must be
    # told to contact support instead of seeing a misleading "check your email".
    try:
        send_account_deletion_email(
            to_email=user.email,
            username=user.first_name or user.email,
            confirmation_link=confirmation_url,
        )
    except Exception as exc:
        # In dev (no Mailgun) every send fails — log the URL so the dev can
        # complete the flow manually. In prod this also gives an admin a way
        # to honor the deletion if the email service is briefly down.
        logger.warning(
            "Account deletion email send failed for user_id=%s. Confirmation URL: %s",
            user.id,
            confirmation_url,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="email_send_failed",
        ) from exc

    log_event(session, action=EventType.USER_DELETE_REQUEST, user_id=user.id, request=request)

    return AuthMessageResponse(message="Confirmation email sent")
