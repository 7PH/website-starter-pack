# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Authentication controller for email verification and password reset.
Extends the core users controller with additional auth features.
"""

import hashlib
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..constants import PASSWORD_MIN_LENGTH, EventType
from ..crud.event_logs import log_event
from ..crud.users import get_user_by_email, get_user_by_id, is_email_taken, soft_delete_user, update_user
from ..helpers.account_deletion import mask_email, resolve_deletion_token
from ..helpers.auth import (
    get_code_validator,
    get_current_user,
    get_user_or_404,
    hash_password,
    issue_jwt_for_user,
    sync_existing_user_to_stripe,
    verify_password,
)
from ..helpers.auth_tokens import (
    create_email_verification_token,
    create_password_reset_token,
    decode_typed_token,
    get_email_verification_url,
    get_password_reset_url,
)
from ..helpers.db import get_session
from ..helpers.email import (
    send_email_verification_email,
    send_password_reset_email,
    swallow_email_errors,
)
from ..helpers.ratelimit import ensure_rate_limit, ensure_user_cooldown_and_daily, get_client_ip
from ..schemas.user import (
    AccountDeletionConfirm,
    AccountDeletionInfo,
    AuthMessageResponse,
    EmailChangeConfirm,
    EmailVerificationConfirm,
    PasswordResetConfirmJWT,
    SignInWithCodeRequest,
    UserPasswordResetRequest,
    UserRead,
    UserTokenUpdate,
)

router = APIRouter()

# Rate limit constants
EMAIL_VERIFICATION_COOLDOWN_MINUTES = 5
EMAIL_VERIFICATION_DAILY_LIMIT = 10
PASSWORD_RESET_COOLDOWN_MINUTES = 5
PASSWORD_RESET_IP_DAILY_LIMIT = 20
AUTH_CODE_RATE_LIMIT_PER_IP_MIN = 10
AUTH_CODE_RATE_LIMIT_PER_IP_DAY = 100
AUTH_CODE_FAILURE_COOLDOWN_MINUTES = 15
AUTH_CODE_FAILURE_THRESHOLD = 5


def _decode_token_and_get_user(session: Session, token: str, token_type: str):
    """Decode a typed JWT and load its user, raising 400/404 on failure."""
    payload = decode_typed_token(token, token_type)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user = get_user_or_404(session, payload["user_id"])
    return payload, user


@router.post(
    "/email-verifications",
    response_model=AuthMessageResponse,
    status_code=status.HTTP_200_OK,
)
def send_verification_email(
    *,
    request: Request,
    session: Session = Depends(get_session),
    current_user: UserRead = Depends(get_current_user),
):
    """
    Send (or resend) email verification to the current user.
    Requires authentication. Rate limited per-user.
    """
    user = get_user_by_id(session, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.email_confirmed:
        raise HTTPException(status_code=400, detail="Email already verified")

    ensure_user_cooldown_and_daily(
        action="send-verification-email",
        user_id=user.id,
        cooldown_minutes=EMAIL_VERIFICATION_COOLDOWN_MINUTES,
        daily_quota=EMAIL_VERIFICATION_DAILY_LIMIT,
    )

    # Generate token and send email
    token = create_email_verification_token(user.id, user.email)
    verification_url = get_email_verification_url(token)

    with swallow_email_errors():
        send_email_verification_email(
            to_email=user.email,
            username=user.first_name,
            verification_link=verification_url,
        )

    # Update sent_at timestamp if the column exists
    if hasattr(user, "email_verification_sent_at"):
        user.email_verification_sent_at = datetime.now(UTC)
        update_user(session, user)

    return AuthMessageResponse(message="Verification email sent")


@router.post(
    "/email-verifications/confirm",
    response_model=AuthMessageResponse,
    status_code=status.HTTP_200_OK,
)
def verify_email(
    *,
    session: Session = Depends(get_session),
    body: EmailVerificationConfirm,
):
    """
    Verify email address using the token from the verification email.
    Token is a JWT containing user_id, email, type, exp.
    """
    payload, user = _decode_token_and_get_user(session, body.token, "verify-email")

    # Ensure the email in the token matches current user email
    # This invalidates old tokens if user changed their email
    if user.email != payload["email"]:
        raise HTTPException(status_code=400, detail="Token email does not match current email")

    if user.email_confirmed:
        return AuthMessageResponse(message="Email already verified")

    user.email_confirmed = True
    update_user(session, user)

    # Log email verification
    log_event(session, action=EventType.USER_EMAIL_VERIFY, user_id=user.id)

    return AuthMessageResponse(message="Email verified successfully")


@router.post(
    "/password-resets",
    response_model=AuthMessageResponse,
    status_code=status.HTTP_200_OK,
)
def request_password_reset(
    *,
    request: Request,
    session: Session = Depends(get_session),
    body: UserPasswordResetRequest,
):
    """
    Request a password reset email.
    Always returns success to prevent email enumeration.
    """
    email = body.email.lower()

    # Rate limit: per-email cooldown
    ensure_rate_limit(
        action="password-reset-request",
        quota=1,
        key=email,
        duration_minutes=PASSWORD_RESET_COOLDOWN_MINUTES,
    )

    # Rate limit: per-IP daily limit
    ensure_rate_limit(
        action="password-reset-request-ip-daily",
        quota=PASSWORD_RESET_IP_DAILY_LIMIT,
        key=get_client_ip(request),
        duration_minutes=60 * 24,
    )

    user = get_user_by_email(session, email)

    # Always return success to prevent email enumeration. We also silently
    # skip non-password users here (oauth, access_code, deleted) — they have
    # no password to reset, but we don't want to leak that fact.
    if user and user.auth_method == "password":
        token = create_password_reset_token(user.id)
        reset_url = get_password_reset_url(token)

        with swallow_email_errors():
            send_password_reset_email(
                to_email=user.email,
                username=user.first_name,
                reset_link=reset_url,
            )

        # Log password reset request
        log_event(session, action=EventType.USER_PASSWORD_RESET_REQUEST, user_id=user.id, request=request)

    return AuthMessageResponse(message="If an account exists, a reset email has been sent")


@router.post(
    "/password-resets/confirm",
    response_model=AuthMessageResponse,
    status_code=status.HTTP_200_OK,
)
def reset_password(
    *,
    request: Request,
    session: Session = Depends(get_session),
    body: PasswordResetConfirmJWT,
):
    """
    Reset password using the JWT token from the reset email.
    """
    _, user = _decode_token_and_get_user(session, body.token, "reset-password")

    # Reject non-password accounts: even a leaked reset token shouldn't be able
    # to graft a password onto an oauth/access_code/deleted user.
    if user.auth_method != "password":
        raise HTTPException(status_code=400, detail="Password reset is not available for this account")

    if len(body.password) < PASSWORD_MIN_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Password must be at least {PASSWORD_MIN_LENGTH} characters",
        )

    user.hashed_password = hash_password(body.password)
    update_user(session, user)

    # Log password reset
    log_event(session, action=EventType.USER_PASSWORD_RESET, user_id=user.id, request=request)

    return AuthMessageResponse(message="Password reset successfully")


@router.post(
    "/email-changes/confirm",
    response_model=AuthMessageResponse,
    status_code=status.HTTP_200_OK,
)
def confirm_email_change(
    *,
    session: Session = Depends(get_session),
    body: EmailChangeConfirm,
):
    """
    Confirm email change using the JWT token from the confirmation email.
    Token contains user_id, current_email, new_email, exp.
    """
    payload, user = _decode_token_and_get_user(session, body.token, "change-email")

    # Ensure the current_email in the token matches user's current email
    # This invalidates old tokens if user requested another email change
    if user.email != payload["current_email"]:
        raise HTTPException(status_code=400, detail="Token is no longer valid (email was changed)")

    new_email = payload["new_email"]

    # Double-check the new email is still available
    if is_email_taken(session, new_email):
        raise HTTPException(status_code=409, detail="Email is no longer available")

    # Apply the email change
    user.email = new_email
    user.email_confirmed = True  # Already verified by clicking the link
    update_user(session, user)

    sync_existing_user_to_stripe(user)

    # Log email change
    log_event(
        session,
        action=EventType.USER_PROFILE_UPDATE,
        user_id=user.id,
        details={"action": "email_changed", "new_email": new_email},
    )

    return AuthMessageResponse(message="Email changed successfully")


@router.get(
    "/account-deletions/info",
    response_model=AccountDeletionInfo,
    status_code=status.HTTP_200_OK,
)
def account_deletion_info(
    *,
    session: Session = Depends(get_session),
    token: str,
):
    """Decode the deletion token and return enough info to render the confirm page."""
    user, _ = resolve_deletion_token(session, token)
    if user.auth_method == "access_code":
        # Managed accounts can't self-delete; their group owner removes them.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not available for managed accounts")
    return AccountDeletionInfo(
        # Only password users have a password to re-enter; oauth users
        # authenticate by token alone.
        requires_password=user.auth_method == "password",
        email_masked=mask_email(user.email or ""),
    )


@router.post(
    "/account-deletions/confirm",
    status_code=status.HTTP_204_NO_CONTENT,
)
def confirm_account_deletion(
    *,
    request: Request,
    session: Session = Depends(get_session),
    body: AccountDeletionConfirm,
):
    """
    Confirm account deletion. Token authorizes the request; password-auth users
    must also re-enter their password. OAuth-only users skip the password step.
    """
    user, _ = resolve_deletion_token(session, body.token)

    if user.auth_method == "access_code":
        # Belt-and-suspenders: managed accounts can't reach this token in the
        # first place because /users/me/account-deletions blocks them upstream.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not available for managed accounts")

    # Password users must re-enter their password. OAuth users authenticate
    # by token alone.
    if user.auth_method == "password" and (
        not body.password or not verify_password(body.password, user.hashed_password or "")
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    # Log before anonymization so the original user_id is captured
    log_event(session, action=EventType.USER_DELETE_COMPLETE, user_id=user.id, request=request)

    soft_delete_user(session, user)


@router.post(
    "/auth/code",
    response_model=UserTokenUpdate,
    status_code=status.HTTP_200_OK,
)
def sign_in_with_code(
    *,
    request: Request,
    session: Session = Depends(get_session),
    body: SignInWithCodeRequest,
):
    """Exchange an access code for a JWT.

    The code lives in the JSON body (not the URL path) so it stays out of
    Traefik access logs, browser history and Referer headers. Apps register
    a validator via `register_code_validator(...)` from main_ext.py; without
    a validator this endpoint returns 404 (it's effectively not configured).
    """
    validator = get_code_validator()
    if validator is None:
        # Fail closed: behave as if the route doesn't exist for apps that
        # didn't opt in. Avoids the misconfiguration of "endpoint up but
        # no validator wired" silently accepting things.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")

    client_ip = get_client_ip(request)

    # Per-IP rate limit: minute and day windows. Single-replica today, so the
    # in-process limiter is fine; revisit when scaling out.
    ensure_rate_limit(
        action="auth-code",
        quota=AUTH_CODE_RATE_LIMIT_PER_IP_MIN,
        key=client_ip,
        duration_minutes=1,
    )
    ensure_rate_limit(
        action="auth-code-daily",
        quota=AUTH_CODE_RATE_LIMIT_PER_IP_DAY,
        key=client_ip,
        duration_minutes=60 * 24,
    )

    user = validator(body.managed_account_id, body.code, request)
    if user is None:
        # Bucket failure cooldowns per (IP, account_id) instead of IP alone so
        # one user typo'ing on a school NAT doesn't lock out the rest, and so
        # an attacker can't fan out across many accounts from a single IP.
        bucket_key = f"{client_ip}:{body.managed_account_id}"
        ensure_rate_limit(
            action="auth-code-fail",
            quota=AUTH_CODE_FAILURE_THRESHOLD,
            key=bucket_key,
            duration_minutes=AUTH_CODE_FAILURE_COOLDOWN_MINUTES,
        )
        # Log a hash of the code, never the code itself.
        code_hash = hashlib.sha256(body.code.encode("utf-8")).hexdigest()[:12]
        log_event(
            session,
            action=EventType.USER_LOGIN_CODE_FAIL,
            request=request,
            details={"managed_account_id": body.managed_account_id, "code_hash": code_hash},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid code")

    log_event(session, action=EventType.USER_LOGIN_CODE, user_id=user.id, request=request)
    return issue_jwt_for_user(session, user)
