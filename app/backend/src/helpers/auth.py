# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ..constants import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
)
from ..models.managed_account_group import ManagedAccountGroupBase
from ..models.user import UserBase
from ..schemas.user import UserRead, UserTokenUpdate
from .db import get_session
from .exception import InvalidTokenException
from .user_display import billing_name

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


def hash_password(password: str) -> str:
    """
    Hash the password using bcrypt with automatic salt generation.
    Uses cost factor of 12 (2^12 iterations) for security.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify if the provided password matches the bcrypt hashed password.
    """
    try:
        password_bytes = password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except (ValueError, TypeError):
        # Invalid hash format
        return False


def get_token_user(session: Session, payload: dict) -> UserBase:
    """The DB row behind a decoded access token, or 401 when the account is gone or its sessions were revoked."""
    from ..crud.users import get_user_by_id

    data = payload.get("data", {})
    user = get_user_by_id(session, payload["id"])
    # Tokens minted before token_version existed carry no claim and match the column default.
    if not user or user.token_version != data.get("token_version", 0):
        raise InvalidTokenException("Session expired, please sign in again")
    # An impersonation token dies with the admin rights of whoever started it.
    if real_admin_id := data.get("real_admin_id"):
        admin = get_user_by_id(session, real_admin_id)
        if not admin or not admin.is_admin:
            raise InvalidTokenException("Session expired, please sign in again")
    return user


def revoke_sessions(user: UserBase) -> None:
    """Invalidate every token issued to the user so far. The caller commits."""
    user.token_version += 1


def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> UserRead:
    """
    Get the current user from the JWT token, checked against the DB.

    The row has the final say on is_admin, email and email_confirmed. is_premium
    stays the claim: managed accounts inherit their owner's at mint time.
    """
    token_decoded = decode_access_token(token)
    user = get_token_user(session, token_decoded)
    data = token_decoded.get("data", {})
    return UserRead(
        id=user.id,
        email=user.email,
        email_confirmed=bool(user.email_confirmed),
        username=data.get("username"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        display_name=data.get("display_name"),
        is_admin=bool(user.is_admin),
        is_premium=data.get("is_premium") or False,
        auth_method=data.get("auth_method", "password"),
        managed_account_group_id=data.get("managed_account_group_id"),
    )


async def get_current_admin(current_user: UserRead = Depends(get_current_user)) -> UserRead:
    """Get the current user, requiring admin privileges (``is_admin`` comes from the DB)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def get_current_nonmanaged_user(user: UserRead = Depends(get_current_user)) -> UserRead:
    """403 when the caller is a managed account (auth_method='access_code').

    Wire onto routes that mutate billing, org membership, or self-identity —
    things a code-only kid identity has no business doing. Compose with
    ``get_current_user`` (this dependency is a strict superset).
    """
    if user.auth_method == "access_code":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action isn't available to managed accounts.",
        )
    return user


def sync_existing_user_to_stripe(user: UserBase) -> None:
    """Push the user's current name/email to their Stripe customer record.

    No-op if Stripe is disabled or the user has no stripe_id yet (use
    :func:`setup_new_user_stripe` for the create path).
    """
    from . import stripe as stripe_helper

    if stripe_helper.is_enabled() and user.stripe_id:
        stripe_helper.sync_customer(
            user_id=user.id,
            email=user.email,
            name=billing_name(user),
            existing_stripe_id=user.stripe_id,
        )


def setup_new_user_stripe(session: Session, user: UserBase, *, allow_orphan_reuse: bool = True) -> None:
    """Create a Stripe customer record for a freshly-created user.

    ``allow_orphan_reuse=True`` lets the Stripe helper reuse a customer record
    whose linked DB user has been deleted; pass ``False`` for OAuth flows where
    a fresh customer record is preferable.

    Does NOT create a subscription — the user becomes premium only after
    going through ``POST /stripe/checkout``. (The starterpack used to
    auto-create a $0 subscription here; removed in v3.4.0 as part of the
    cleaner subscribe / manage split.)
    """
    from ..crud.users import get_user_by_id, update_user
    from . import stripe as stripe_helper

    if not stripe_helper.is_enabled():
        return
    check_user_exists = (
        (lambda uid: get_user_by_id(session, uid) is not None) if allow_orphan_reuse else (lambda uid: True)
    )
    user.stripe_id = stripe_helper.sync_customer(
        user_id=user.id,
        email=user.email,
        name=billing_name(user),
        check_user_exists=check_user_exists,
    )
    update_user(session, user)


def get_user_or_404(session: Session, user_id: int, *, include_deleted: bool = False) -> UserBase:
    """Look up a user and raise 404 if missing.

    Centralized so controllers don't repeat the get + raise pattern. Pass
    ``include_deleted=True`` for admin endpoints that need to inspect
    soft-deleted accounts.
    """
    from ..crud.users import get_user_by_id

    user = get_user_by_id(session, user_id, include_deleted=include_deleted)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def is_premium_effective(session: Session, user: UserBase) -> bool:
    """Return the premium status to use for entitlement decisions.

    For managed accounts (``auth_method='access_code'``), inherits from the
    group's owner — kids don't subscribe themselves, but they get whatever
    their manager paid for. For everyone else, uses the user's own flag.

    Apps shipping a server-side ``require_premium`` dependency should call
    this against a fresh DB row, not the JWT claim, so the entitlement check
    survives mid-session changes (e.g. owner cancels Stripe).
    """
    # Hot path: non-managed users use their own flag, no DB lookup.
    if user.auth_method != "access_code" or user.managed_account_group_id is None:
        return bool(user.is_premium)
    group = session.get(ManagedAccountGroupBase, user.managed_account_group_id)
    if group is None:
        return False
    owner = session.get(UserBase, group.owner_id)
    return bool(owner and owner.is_premium and owner.deleted_at is None)


def build_user_read_with_orgs(session: Session, user: UserBase) -> UserRead:
    """Build a UserRead with org memberships and effective premium.

    Computes ``is_premium`` via :func:`is_premium_effective` so managed
    accounts inherit from their group owner. Used by every endpoint that
    mints a fresh token.

    Also fires ``UserReadAssembled`` so app-side fields land in
    ``UserRead.extra``, both on token mint and on ``GET /users/me``.
    """
    from ..constants import ORGANIZATIONS_ENABLED
    from ..crud.organizations import get_user_organizations
    from ..schemas.organization import UserOrganizationInfo
    from ..schemas.user_ext import UserCustomData
    from .hooks import UserReadAssembled, fire

    organizations: list[UserOrganizationInfo] = []
    if ORGANIZATIONS_ENABLED:
        memberships = get_user_organizations(session, user.id)
        organizations = [
            UserOrganizationInfo(
                organization_id=m.organization_id,
                organization_name=m.organization.name if m.organization else "Unknown",
                is_admin=m.is_admin,
                has_premium_seat=m.has_premium_seat,
            )
            for m in memberships
            if m.organization and not m.organization.deleted_at
        ]
    user_read = UserRead(
        id=user.id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        display_name=user.display_name,
        email_confirmed=bool(user.email_confirmed),
        is_admin=user.is_admin,
        is_premium=is_premium_effective(session, user),
        has_personal_subscription=user.has_personal_subscription,
        auth_method=user.auth_method,
        managed_account_group_id=user.managed_account_group_id,
        custom_data=UserCustomData(**(user.custom_data or {})),
        organizations=organizations,
    )
    event = fire(session, UserReadAssembled(user=user_read))
    user_read.extra = event.extra
    return user_read


def _get_data_claim(token: str, key: str) -> int | None:
    return decode_access_token(token)["data"].get(key)


async def get_real_admin_id(token: str = Depends(oauth2_scheme)) -> int | None:
    """Real admin ID from an impersonation token, or None if not impersonating."""
    return _get_data_claim(token, "real_admin_id")


async def get_parent_user_id(token: str = Depends(oauth2_scheme)) -> int | None:
    """Owner ID from an "open as managed account" token, or None if not in that flow."""
    return _get_data_claim(token, "parent_user_id")


def create_access_token(
    user: UserRead,
    *,
    token_version: int,
    impersonating_as: UserRead | None = None,
    open_as_managed_account: UserRead | None = None,
) -> UserTokenUpdate:
    """
    Create a new JWT access token for the given user.

    `sub` carries str(user.id) so that email-less users (auth_method='access_code')
    still produce a valid OAuth2 token. The user's email (if any) lives in data.email.

    Args:
        user: The user to create the token for (the owner when open_as / the admin when impersonating)
        token_version: DB token_version of the user the token represents (the target when impersonating / open_as)
        impersonating_as: If set, admin-impersonation token for this user
        open_as_managed_account: If set, owner-initiated "open as" token for this managed account
    """
    now = datetime.now(UTC)
    exp = now + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    # When impersonating or open-as, the token represents the target user.
    effective_user = impersonating_as or open_as_managed_account or user

    encoded_data = {
        "id": effective_user.id,
        "sub": str(effective_user.id),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "data": {
            "token_version": token_version,
            "email": effective_user.email,
            "username": effective_user.username,
            "first_name": effective_user.first_name,
            "last_name": effective_user.last_name,
            "display_name": effective_user.display_name,
            "is_admin": effective_user.is_admin,
            "is_premium": effective_user.is_premium,
            "auth_method": effective_user.auth_method,
            "managed_account_group_id": effective_user.managed_account_group_id,
            # Admin impersonation marker (admin opening any user).
            "real_admin_id": user.id if impersonating_as else None,
            # Owner "open as" marker (group owner opening one of their managed accounts).
            "parent_user_id": user.id if open_as_managed_account else None,
        },
    }

    encoded_jwt = jwt.encode(encoded_data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    token_parsed = dict(
        user=effective_user,
        created_at=now,
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


# ---------------------------------------------------------------------------
# Sign-in-by-code: pluggable resolver
#
# POST /auth/code is driven by the AccessCodeResolution event. Sub-apps
# register a handler from main_ext.py:
#
#     from .helpers.hooks import AccessCodeResolution, on
#
#     @on(AccessCodeResolution)
#     def my_resolver(session, event):
#         if event.user is None:
#             event.user = lookup_by_code(session, event.managed_account_id, event.code)
# ---------------------------------------------------------------------------


def issue_jwt_with_orgs(session: Session, user: UserBase) -> UserTokenUpdate:
    """Mint an access token whose UserRead includes the user's org memberships."""
    return create_access_token(build_user_read_with_orgs(session, user), token_version=user.token_version)


def issue_jwt_for_user(session: Session, user: UserBase) -> UserTokenUpdate:
    """Build a UserRead from a DB row and mint an access token.

    Used by the access-code endpoint; mirrors what login_user does for password
    auth, minus the org membership lookup (access-code users typically aren't
    org members; apps that need this can call create_access_token directly).

    Resolves the user's *effective* premium status (managed accounts inherit
    from their group's owner) before minting, so the JWT carries the value
    the frontend should render and the value server-side checks should match.
    """
    user_read = UserRead.model_validate(user)
    user_read.is_premium = is_premium_effective(session, user)
    return create_access_token(user_read, token_version=user.token_version)
