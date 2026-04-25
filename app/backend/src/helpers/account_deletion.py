# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Helpers for the self-service account-deletion flow."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..crud.users import get_user_by_id
from ..models.user import UserBase
from .auth_tokens import decode_typed_token


def resolve_deletion_token(session: Session, token: str) -> tuple[UserBase, dict]:
    """Decode an account-deletion token and load the target user.

    Raises 401 if the token is invalid/expired, the user is missing, or the
    email captured at request time has changed since.
    """
    payload = decode_typed_token(token, "delete-account")
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired link")

    user = get_user_by_id(session, payload["user_id"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired link")

    if user.email != payload.get("email_at_request"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired link")

    return user, payload


def mask_email(email: str) -> str:
    """Mask the local part of an email for display: 'alice@x.com' -> 'a***@x.com'."""
    if not email or "@" not in email:
        return ""
    local, _, domain = email.partition("@")
    if len(local) <= 1:
        return f"{local}***@{domain}"
    return f"{local[0]}***@{domain}"
