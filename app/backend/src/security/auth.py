import datetime
import os
from typing import Optional

import bcrypt
import jwt
from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..model.db import User, UserRead, UserToken

security = HTTPBearer(auto_error=False)


def get_token(
    authorization: HTTPAuthorizationCredentials = Security(security),
) -> UserToken:
    # Ensure header is set
    if not authorization or not authorization.credentials:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas connecté")

    # Retrieve raw token
    raw_token = authorization.credentials
    if not raw_token:
        raise HTTPException(status_code=403, detail="Token incorrect")

    # Try to decode token
    token = jwt.decode(
        raw_token,
        os.environ["TOKEN_HASH_SECRET"],
        algorithms=[os.environ["TOKEN_HASH_ALG"]],
    )
    if not token:
        raise HTTPException(status_code=403, detail="Token incorrect")

    # Token expired
    if datetime.datetime.fromisoformat(token["expires_at"]) < datetime.datetime.now():
        raise HTTPException(status_code=403, detail="Token expiré")

    return UserToken(**token)


def get_user(
    authorization: HTTPAuthorizationCredentials = Security(security),
) -> UserRead:
    token = get_token(authorization)
    return token.user


def get_user_admin(
    authorization: HTTPAuthorizationCredentials = Security(security),
) -> UserRead:
    token = get_token(authorization)
    if not token.user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    return token.user


def get_user_optional(
    authorization: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> UserRead:
    if not authorization:
        return None
    token = get_token(authorization)
    return token.user


def get_ip(request: Request):
    return request.client.host


def generate_token(user: User, validity_days: int) -> str:
    created_at = datetime.datetime.now()
    expires_at = created_at + datetime.timedelta(days=validity_days)
    return jwt.encode(
        {
            "type": "auth",
            "user": UserRead(**user.dict()).dict(),
            "created_at": str(created_at),
            "expires_at": str(expires_at),
        },
        os.environ["TOKEN_HASH_SECRET"],
        algorithm=os.environ["TOKEN_HASH_ALG"],
    )


def decode_token(token: str) -> Optional[UserToken]:
    return jwt.decode(
        token,
        os.environ["TOKEN_HASH_SECRET"],
        algorithms=[os.environ["TOKEN_HASH_ALG"]],
    )


def hash_password(password: str) -> str:
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    return hashed_password


def verify_hashed_password(to_verify: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(to_verify.encode(), hashed_password.encode())


def generate_password_reset_token() -> str:
    # Generate a random token of alphanumeric characters
    return os.urandom(32).hex()
