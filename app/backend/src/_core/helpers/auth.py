import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from ..constant import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    PASSWORD_HASH_SECRET_KEY,
)
from ..exception import InvalidTokenException
from ..resources.users.model import UserBase, UserRead, UserTokenUpdate

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def hash_password(password: str) -> str:
    """
    Hash the password using HMAC with a secret key.
    """
    return hmac.new(
        PASSWORD_HASH_SECRET_KEY, password.encode("utf-8"), hashlib.sha256
    ).hexdigest()


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
    )


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[UserBase]:
    """
    Retrieve the current user if the token is provided, otherwise return None.
    If no token is passed, the user is considered unauthenticated.
    """
    return get_current_user(token) if token else None


def create_access_token(user: UserRead) -> UserTokenUpdate:
    """
    Create a new JWT access token for the given user.

    Generates a JWT with the user's ID, email, and expiration time, and additional custom data.
    """
    exp = datetime.now(timezone.utc) + timedelta(
        minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    # Top-level claims and additional data
    encoded_data = {
        "id": user.id,  # Top-level claim for user ID
        "sub": user.email,  # OAuth2 subject (typically email or UUID)
        "exp": int(exp.timestamp()),  # Expiration timestamp
        "data": {  # Encapsulated custom claims
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_admin": user.is_admin,
        },
    }

    encoded_jwt = jwt.encode(encoded_data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    token_parsed = dict(
        user=user,
        created_at=datetime.now(timezone.utc),
        expires_at=exp,
    )

    return UserTokenUpdate(
        token_parsed=token_parsed, access_token=encoded_jwt, user=user
    )


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Returns the token's payload if valid, otherwise raises an exception if the token is expired or invalid.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise InvalidTokenException("Token has expired")
    except jwt.InvalidTokenError:
        raise InvalidTokenException("Invalid token")


def generate_password_reset_token() -> str:
    """
    Generate a password reset token using a secure random URL-safe string.
    """
    return os.urandom(32).hex()
