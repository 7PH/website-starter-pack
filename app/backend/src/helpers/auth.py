# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import hashlib
import hmac
import os
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from ..constants import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    PASSWORD_HASH_SECRET_KEY,
)
from ..models.user import UserBase, UserRead, UserTokenUpdate
from .exception import InvalidTokenException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def hash_password(password: str) -> str:
    """
    Hash the password using HMAC with a secret key.
    """
    return hmac.new(PASSWORD_HASH_SECRET_KEY, password.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify if the provided password matches the hashed password.
    """
    return hmac.compare_digest(hashed_password, hash_password(password))


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserRead:
    """
    Get the current user from the JWT token.

    Decodes the JWT, retrieves the user by email, and returns the user.
    If the user is not found or the token is invalid, raises an exception.
    """
    token_decoded = decode_access_token(token)
    return UserRead(
        id=token_decoded["id"],
        email=token_decoded["sub"],
        first_name=token_decoded["data"].get("first_name"),
        last_name=token_decoded["data"].get("last_name"),
        is_admin=token_decoded["data"].get("is_admin"),
        is_premium=token_decoded["data"].get("is_premium"),
    )


async def get_current_admin(current_user: UserRead = Depends(get_current_user)) -> UserRead:
    """
    Get the current user, requiring admin privileges.

    Raises HTTPException 403 if the user is not an admin.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def get_real_admin_id(token: str = Depends(oauth2_scheme)) -> int | None:
    """
    Get the real admin ID from an impersonation token.

    Returns the real_admin_id if the token contains impersonation info, else None.
    """
    token_decoded = decode_access_token(token)
    return token_decoded["data"].get("real_admin_id")


def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
) -> UserBase | None:
    """
    Retrieve the current user if the token is provided, otherwise return None.
    If no token is passed, the user is considered unauthenticated.
    """
    return get_current_user(token) if token else None


def create_access_token(
    user: UserRead,
    impersonating_as: UserRead | None = None,
) -> UserTokenUpdate:
    """
    Create a new JWT access token for the given user.

    Generates a JWT with the user's ID, email, and expiration time, and additional custom data.

    Args:
        user: The user to create the token for (the admin when impersonating)
        impersonating_as: If set, the token will contain impersonation info for this user
    """
    exp = datetime.now(UTC) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    # When impersonating, the token represents the target user but tracks the admin
    effective_user = impersonating_as if impersonating_as else user

    # Top-level claims and additional data
    encoded_data = {
        "id": effective_user.id,  # Top-level claim for user ID
        "sub": effective_user.email,  # OAuth2 subject (typically email or UUID)
        "exp": int(exp.timestamp()),  # Expiration timestamp
        "data": {  # Encapsulated custom claims
            "email": effective_user.email,
            "first_name": effective_user.first_name,
            "last_name": effective_user.last_name,
            "is_admin": effective_user.is_admin,
            "is_premium": effective_user.is_premium,
            # Impersonation: if set, this token is for an impersonated user
            "real_admin_id": user.id if impersonating_as else None,
        },
    }

    encoded_jwt = jwt.encode(encoded_data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    token_parsed = dict(
        user=effective_user,
        created_at=datetime.now(UTC),
        expires_at=exp,
        real_admin_id=user.id if impersonating_as else None,
    )

    return UserTokenUpdate(token_parsed=token_parsed, access_token=encoded_jwt, user=effective_user)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Returns the token's payload if valid, otherwise raises an exception if the token is expired or invalid.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise InvalidTokenException("Token has expired") from None
    except jwt.InvalidTokenError:
        raise InvalidTokenException("Invalid token") from None


def generate_password_reset_token() -> str:
    """
    Generate a password reset token using a secure random URL-safe string.
    """
    return os.urandom(32).hex()
