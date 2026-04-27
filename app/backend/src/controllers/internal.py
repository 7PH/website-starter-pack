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
from ..crud.users import get_user_by_email
from ..helpers.auth import build_user_read_with_orgs, create_access_token
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
    return create_access_token(build_user_read_with_orgs(session, user))
