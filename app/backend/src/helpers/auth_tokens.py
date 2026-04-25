# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
JWT token utilities for email verification and password reset.
Uses typed tokens to distinguish between different authentication flows.
"""

from datetime import UTC, datetime, timedelta
from typing import Literal

import jwt

from ..constants import JWT_ALGORITHM, JWT_SECRET_KEY, PUBLIC_URL

# Token expiration constants
EMAIL_VERIFICATION_EXPIRE_DAYS = 10
PASSWORD_RESET_EXPIRE_DAYS = 7
EMAIL_CHANGE_EXPIRE_DAYS = 2
ACCOUNT_DELETION_EXPIRE_MINUTES = 60


def create_email_verification_token(user_id: int, email: str) -> str:
    """
    Create a JWT token for email verification.

    Token contains: type, user_id, email, exp
    The email is included to invalidate tokens if user changes email.
    """
    exp = datetime.now(UTC) + timedelta(days=EMAIL_VERIFICATION_EXPIRE_DAYS)
    payload = {
        "type": "verify-email",
        "user_id": user_id,
        "email": email,
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_password_reset_token(user_id: int) -> str:
    """
    Create a JWT token for password reset.

    Token contains: type, user_id, exp
    """
    exp = datetime.now(UTC) + timedelta(days=PASSWORD_RESET_EXPIRE_DAYS)
    payload = {
        "type": "reset-password",
        "user_id": user_id,
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_email_change_token(user_id: int, current_email: str, new_email: str) -> str:
    """
    Create a JWT token for email change.

    Token contains: type, user_id, current_email, new_email, exp
    The current_email is included to invalidate tokens if user changes email again.
    """
    exp = datetime.now(UTC) + timedelta(days=EMAIL_CHANGE_EXPIRE_DAYS)
    payload = {
        "type": "change-email",
        "user_id": user_id,
        "current_email": current_email,
        "new_email": new_email,
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_account_deletion_token(user_id: int, current_email: str | None) -> str:
    """
    Create a JWT token for account deletion confirmation.

    Token contains: type, user_id, email_at_request, exp.
    The email is captured at request time so the token invalidates if the
    user changes their email between requesting and confirming.
    """
    exp = datetime.now(UTC) + timedelta(minutes=ACCOUNT_DELETION_EXPIRE_MINUTES)
    payload = {
        "type": "delete-account",
        "user_id": user_id,
        "email_at_request": current_email,
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_typed_token(
    token: str,
    expected_type: Literal["verify-email", "reset-password", "change-email", "delete-account"],
) -> dict | None:
    """
    Decode and validate a typed JWT token.

    Returns the payload if valid and type matches, None otherwise.
    This prevents token reuse across different features.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def get_email_verification_url(token: str) -> str:
    """
    Generate the email verification URL with fragment-based token.

    Using fragment (#) instead of query param (?) prevents the token
    from being logged in server access logs.
    """
    base_url = PUBLIC_URL.rstrip("/") if PUBLIC_URL else ""
    return f"{base_url}/verify-email#{token}"


def get_password_reset_url(token: str) -> str:
    """
    Generate the password reset URL with fragment-based token.
    """
    base_url = PUBLIC_URL.rstrip("/") if PUBLIC_URL else ""
    return f"{base_url}/reset-password#{token}"


def get_email_change_url(token: str) -> str:
    """
    Generate the email change confirmation URL with fragment-based token.
    """
    base_url = PUBLIC_URL.rstrip("/") if PUBLIC_URL else ""
    return f"{base_url}/confirm-email-change#{token}"


def get_account_deletion_url(token: str) -> str:
    """
    Generate the account deletion confirmation URL with fragment-based token.
    """
    base_url = PUBLIC_URL.rstrip("/") if PUBLIC_URL else ""
    return f"{base_url}/delete-account#{token}"
