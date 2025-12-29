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


def decode_typed_token(
    token: str,
    expected_type: Literal["verify-email", "reset-password"],
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
