# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Internal endpoints gated by INTERNAL_API_KEY.

Only registered when INTERNAL_API_KEY is set in the environment, so the routes
are invisible (404) in deployments that don't opt in. The key is a master
credential — it can mint a token for any user, admin included — so treat it
like a database password.
"""

import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..constants import INTERNAL_API_KEY
from ..crud.users import create_user, get_user_by_email
from ..helpers.auth import hash_password, issue_jwt_with_orgs
from ..helpers.db import get_session
from ..models.user import UserBase
from ..schemas.user import UserTokenUpdate

router = APIRouter(prefix="/internal")


class MintTokenRequest(BaseModel):
    email: EmailStr | None = None


def _require_internal_key(x_internal_api_key: str = Header(default="")) -> None:
    # Constant-time compare; both branches reject when no server key is set.
    if not INTERNAL_API_KEY or not hmac.compare_digest(x_internal_api_key, INTERNAL_API_KEY):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal API key")


@router.post(
    "/mint-token",
    response_model=UserTokenUpdate,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(_require_internal_key)],
)
def mint_token(*, payload: MintTokenRequest, session: Session = Depends(get_session)) -> UserTokenUpdate:
    if payload.email:
        user = get_user_by_email(session, payload.email.lower())
    else:
        # Fallback for dev tooling: pick the first admin so callers don't need
        # to know an email. Skips soft-deleted rows (email prefixed "deleted_").
        user = (
            session.query(UserBase)
            .filter(UserBase.is_admin.is_(True), ~UserBase.email.like("deleted_%"))
            .order_by(UserBase.id.asc())
            .first()
        )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return issue_jwt_with_orgs(session, user)


class SeedUserSpec(BaseModel):
    email: EmailStr
    password: str
    is_admin: bool = False
    is_premium: bool = False
    first_name: str | None = None
    last_name: str | None = None
    display_name: str | None = None


class SeedUsersRequest(BaseModel):
    users: list[SeedUserSpec]


class SeedUserResult(BaseModel):
    email: EmailStr
    status: str  # "created" | "updated"


class SeedUsersResponse(BaseModel):
    results: list[SeedUserResult]


@router.post(
    "/seed-users",
    response_model=SeedUsersResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(_require_internal_key)],
)
def seed_users(
    *, payload: SeedUsersRequest, session: Session = Depends(get_session)
) -> SeedUsersResponse:
    """Idempotently upsert a roster of password-auth users for preview/dev.

    Same gating as the rest of /internal: the route is unregistered when
    INTERNAL_API_KEY is empty, so prod stacks can't reach it. Always sets
    ``email_confirmed=True`` and ``auth_method='password'`` — seeded users
    skip the email-verification step that signup normally requires.
    """
    results: list[SeedUserResult] = []
    for spec in payload.users:
        email = spec.email.lower()
        existing = get_user_by_email(session, email)
        if existing is not None:
            existing.hashed_password = hash_password(spec.password)
            existing.is_admin = spec.is_admin
            existing.is_premium = spec.is_premium
            existing.first_name = spec.first_name
            existing.last_name = spec.last_name
            existing.display_name = spec.display_name
            existing.email_confirmed = True
            session.commit()
            results.append(SeedUserResult(email=email, status="updated"))
        else:
            user = UserBase(
                email=email,
                hashed_password=hash_password(spec.password),
                is_admin=spec.is_admin,
                is_premium=spec.is_premium,
                first_name=spec.first_name,
                last_name=spec.last_name,
                display_name=spec.display_name,
                email_confirmed=True,
                auth_method="password",
            )
            create_user(session, user)
            results.append(SeedUserResult(email=email, status="created"))
    return SeedUsersResponse(results=results)
