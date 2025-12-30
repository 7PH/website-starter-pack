# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Authentication controller for email verification and password reset.
Extends the core users controller with additional auth features.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..constants import EventType
from ..crud.event_logs import log_event
from ..crud.users import get_user_by_email, get_user_by_id, update_user
from ..helpers.auth import get_current_user, hash_password
from ..helpers.auth_tokens import (
    create_email_verification_token,
    create_password_reset_token,
    decode_typed_token,
    get_email_verification_url,
    get_password_reset_url,
)
from ..helpers.db import get_session
from ..helpers.email import send_email_verification_email, send_password_reset_email
from ..helpers.ratelimit import ensure_rate_limit
from ..models.user import (
    AuthMessageResponse,
    EmailVerificationConfirm,
    PasswordResetConfirmJWT,
    UserPasswordResetRequest,
    UserRead,
)

router = APIRouter()

# Rate limit constants
EMAIL_VERIFICATION_COOLDOWN_MINUTES = 5
EMAIL_VERIFICATION_DAILY_LIMIT = 10
PASSWORD_RESET_COOLDOWN_MINUTES = 5
PASSWORD_RESET_IP_DAILY_LIMIT = 20


@router.post(
    "/auth/send-verification-email",
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

    # Rate limit: per-user cooldown
    ensure_rate_limit(
        action="send-verification-email",
        quota=1,
        key=str(user.id),
        duration_minutes=EMAIL_VERIFICATION_COOLDOWN_MINUTES,
    )

    # Rate limit: per-user daily limit
    ensure_rate_limit(
        action="send-verification-email-daily",
        quota=EMAIL_VERIFICATION_DAILY_LIMIT,
        key=str(user.id),
        duration_minutes=60 * 24,
    )

    # Generate token and send email
    token = create_email_verification_token(user.id, user.email)
    verification_url = get_email_verification_url(token)

    try:  # noqa: SIM105
        send_email_verification_email(
            to_email=user.email,
            username=user.first_name,
            verification_link=verification_url,
        )
    except Exception:
        # Email service might not be configured - that's OK in development
        pass

    # Update sent_at timestamp if the column exists
    if hasattr(user, "email_verification_sent_at"):
        user.email_verification_sent_at = datetime.now(UTC)
        update_user(session, user)

    return AuthMessageResponse(message="Verification email sent")


@router.post(
    "/auth/verify-email",
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
    payload = decode_typed_token(body.token, "verify-email")
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = get_user_by_id(session, payload["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

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
    "/auth/request-password-reset",
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
    client_ip = request.client.host if request.client else "unknown"

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
        key=client_ip,
        duration_minutes=60 * 24,
    )

    user = get_user_by_email(session, email)

    # Always return success to prevent email enumeration
    if user:
        token = create_password_reset_token(user.id)
        reset_url = get_password_reset_url(token)

        try:  # noqa: SIM105
            send_password_reset_email(
                to_email=user.email,
                username=user.first_name,
                reset_link=reset_url,
            )
        except Exception:
            # Email service might not be configured
            pass

        # Log password reset request
        log_event(session, action=EventType.USER_PASSWORD_RESET_REQUEST, user_id=user.id, request=request)

    return AuthMessageResponse(message="If an account exists, a reset email has been sent")


@router.post(
    "/auth/reset-password",
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
    payload = decode_typed_token(body.token, "reset-password")
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = get_user_by_id(session, payload["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate password length
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user.hashed_password = hash_password(body.password)
    update_user(session, user)

    # Log password reset
    log_event(session, action=EventType.USER_PASSWORD_RESET, user_id=user.id, request=request)

    return AuthMessageResponse(message="Password reset successfully")
