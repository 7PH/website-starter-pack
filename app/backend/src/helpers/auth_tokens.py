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


def _encode_typed_token(payload: dict, expires_in: timedelta) -> str:
    exp = datetime.now(UTC) + expires_in
    return jwt.encode({**payload, "exp": int(exp.timestamp())}, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_email_verification_token(user_id: int, email: str) -> str:
    # Email in payload invalidates the token if the user changes address.
    return _encode_typed_token(
        {"type": "verify-email", "user_id": user_id, "email": email},
        timedelta(days=EMAIL_VERIFICATION_EXPIRE_DAYS),
    )


def create_password_reset_token(user_id: int) -> str:
    return _encode_typed_token(
        {"type": "reset-password", "user_id": user_id},
        timedelta(days=PASSWORD_RESET_EXPIRE_DAYS),
    )


def create_email_change_token(user_id: int, current_email: str, new_email: str) -> str:
    # current_email in payload invalidates the token on subsequent email changes.
    return _encode_typed_token(
        {"type": "change-email", "user_id": user_id, "current_email": current_email, "new_email": new_email},
        timedelta(days=EMAIL_CHANGE_EXPIRE_DAYS),
    )


def create_account_deletion_token(user_id: int, current_email: str | None) -> str:
    # email_at_request invalidates the token if the user changes address mid-flow.
    return _encode_typed_token(
        {"type": "delete-account", "user_id": user_id, "email_at_request": current_email},
        timedelta(minutes=ACCOUNT_DELETION_EXPIRE_MINUTES),
    )


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


def _build_token_url(path: str, token: str) -> str:
    """Build a URL with the token in the fragment, not the query string.

    Fragments aren't sent to the server, so the token never appears in
    access logs or upstream proxies.
    """
    base_url = PUBLIC_URL.rstrip("/") if PUBLIC_URL else ""
    return f"{base_url}{path}#{token}"


def get_email_verification_url(token: str) -> str:
    return _build_token_url("/verify-email", token)


def get_password_reset_url(token: str) -> str:
    return _build_token_url("/reset-password", token)


def get_email_change_url(token: str) -> str:
    return _build_token_url("/confirm-email-change", token)


def get_account_deletion_url(token: str) -> str:
    return _build_token_url("/delete-account", token)
