# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Endpoints for managed account groups and the managed accounts inside them.

Owners (regular users) provision groups and managed accounts. Managed accounts
themselves never use these endpoints — they sign in via /auth/code after
picking their name from the public picker at GET /c/:share_token.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..constants import MANAGED_ACCOUNT_GROUP_MAX_PER_USER, MANAGED_ACCOUNTS_MAX_PER_USER
from ..crud.managed_account_groups import (
    bulk_create_managed_accounts,
    count_accounts_for_owner,
    count_accounts_in_group,
    count_groups_for_owner,
    create_group,
    create_managed_account,
    delete_group,
    get_active_code_for_account,
    get_group,
    get_group_by_share_token,
    get_managed_account,
    list_accounts_in_group,
    list_groups_for_owner,
    reissue_managed_account_code,
    rotate_share_token,
    update_group,
    update_managed_account,
)
from ..crud.users import soft_delete_user
from ..helpers.auth import create_access_token, is_premium_effective
from ..helpers.db import get_session
from ..helpers.hooks import ManagedAccountSeatGate, fire
from ..helpers.policies import get_user_with_manage_groups_perm
from ..models.managed_account_group import ManagedAccountGroupBase
from ..models.user import UserBase
from ..schemas.managed_account import (
    ManagedAccountBulkCreate,
    ManagedAccountBulkCreated,
    ManagedAccountCreate,
    ManagedAccountCreated,
    ManagedAccountGroupCreate,
    ManagedAccountGroupRead,
    ManagedAccountGroupUpdate,
    ManagedAccountRead,
    ManagedAccountUpdate,
    PublicPickerEntry,
    PublicPickerPayload,
)
from ..schemas.user import UserRead, UserTokenUpdate

router = APIRouter()


# ─── helpers ───


def _read_group(group: ManagedAccountGroupBase, member_count: int) -> ManagedAccountGroupRead:
    return ManagedAccountGroupRead(
        id=group.id,
        owner_id=group.owner_id,
        name=group.name,
        share_token=group.share_token,
        created_at=group.created_at,
        archived_at=group.archived_at,
        member_count=member_count,
    )


def _read_account(account: UserBase, code: str | None) -> ManagedAccountRead:
    return ManagedAccountRead(
        id=account.id,
        display_name=account.display_name,
        managed_account_group_id=account.managed_account_group_id,
        created_at=account.created_at,
        code=code,
    )


def _require_owned_group(
    session: Session,
    group_id: int,
    user_id: int,
) -> ManagedAccountGroupBase:
    group = get_group(session, group_id)
    if group is None or group.owner_id != user_id:
        # Don't leak existence of groups owned by others.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group


def _require_owned_account(
    session: Session,
    account_id: int,
    user_id: int,
) -> UserBase:
    account = get_managed_account(session, account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    group = get_group(session, account.managed_account_group_id)
    if group is None or group.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


# ─── group endpoints ───


@router.get("/me/managed-account-groups", response_model=list[ManagedAccountGroupRead])
def list_my_groups(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_user_with_manage_groups_perm),
):
    groups = list_groups_for_owner(session, user.id)
    return [_read_group(g, count_accounts_in_group(session, g.id)) for g in groups]


@router.post(
    "/me/managed-account-groups",
    response_model=ManagedAccountGroupRead,
    status_code=status.HTTP_201_CREATED,
)
def create_my_group(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_user_with_manage_groups_perm),
    body: ManagedAccountGroupCreate,
):
    if count_groups_for_owner(session, user.id) >= MANAGED_ACCOUNT_GROUP_MAX_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You can only have up to {MANAGED_ACCOUNT_GROUP_MAX_PER_USER} groups",
        )
    group = create_group(session, owner_id=user.id, name=body.name)
    return _read_group(group, 0)


@router.patch("/me/managed-account-groups/{group_id}", response_model=ManagedAccountGroupRead)
def update_my_group(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_user_with_manage_groups_perm),
    group_id: int,
    body: ManagedAccountGroupUpdate,
):
    group = _require_owned_group(session, group_id, user.id)
    update_group(session, group, name=body.name, archived=body.archived)
    return _read_group(group, count_accounts_in_group(session, group.id))


@router.delete("/me/managed-account-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_group(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_user_with_manage_groups_perm),
    group_id: int,
):
    group = _require_owned_group(session, group_id, user.id)
    delete_group(session, group)


@router.post(
    "/me/managed-account-groups/{group_id}/rotate-token",
    response_model=ManagedAccountGroupRead,
)
def rotate_my_group_token(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_user_with_manage_groups_perm),
    group_id: int,
):
    group = _require_owned_group(session, group_id, user.id)
    rotate_share_token(session, group)
    return _read_group(group, count_accounts_in_group(session, group.id))


# ─── managed account endpoints ───


@router.get(
    "/me/managed-account-groups/{group_id}/managed-accounts",
    response_model=list[ManagedAccountRead],
)
def list_accounts(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_user_with_manage_groups_perm),
    group_id: int,
):
    _require_owned_group(session, group_id, user.id)
    accounts = list_accounts_in_group(session, group_id)
    return [_read_account(a, get_active_code_for_account(session, a.id)) for a in accounts]


@router.post(
    "/me/managed-account-groups/{group_id}/managed-accounts",
    response_model=ManagedAccountCreated,
    status_code=status.HTTP_201_CREATED,
)
def create_account(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_user_with_manage_groups_perm),
    group_id: int,
    body: ManagedAccountCreate,
):
    _require_owned_group(session, group_id, user.id)
    if count_accounts_for_owner(session, user.id) >= MANAGED_ACCOUNTS_MAX_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You can only have up to {MANAGED_ACCOUNTS_MAX_PER_USER} managed accounts in total",
        )

    gate = fire(
        session,
        ManagedAccountSeatGate(user=user, group_id=group_id, count_to_create=1),
    )
    if not gate.allow:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=gate.reason or "Seat quota exceeded",
        )

    account, code = create_managed_account(
        session,
        group_id=group_id,
        display_name=body.display_name,
    )
    return ManagedAccountCreated(account=_read_account(account, code), code=code)


@router.post(
    "/me/managed-account-groups/{group_id}/managed-accounts/bulk",
    response_model=ManagedAccountBulkCreated,
    status_code=status.HTTP_201_CREATED,
)
def bulk_create_accounts(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_user_with_manage_groups_perm),
    group_id: int,
    body: ManagedAccountBulkCreate,
):
    """Bulk-create managed accounts. Duplicates (in-batch and against existing)
    are silently skipped; the response counts them under `skipped`.

    Hard quota check happens on the *unique* incoming names — we don't reject
    a 200-item batch that's mostly dups against existing rows.
    """
    _require_owned_group(session, group_id, user.id)

    current_count = count_accounts_for_owner(session, user.id)
    # Cheap upper bound: even if zero dedup, this is the worst case.
    if current_count + len(body.accounts) > MANAGED_ACCOUNTS_MAX_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"This batch would exceed your {MANAGED_ACCOUNTS_MAX_PER_USER} "
                f"managed-account quota ({current_count} already present)."
            ),
        )

    # App-side per-tier quota gate. Worst-case count (pre-dedup) so handlers
    # see the same upper bound the env-cap check uses.
    gate = fire(
        session,
        ManagedAccountSeatGate(
            user=user,
            group_id=group_id,
            count_to_create=len(body.accounts),
        ),
    )
    if not gate.allow:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=gate.reason or "Seat quota exceeded",
        )

    created, skipped = bulk_create_managed_accounts(
        session,
        group_id=group_id,
        display_names=[a.display_name for a in body.accounts],
    )
    return ManagedAccountBulkCreated(
        accounts=[_read_account(u, c) for u, c in created],
        skipped=skipped,
    )


@router.patch("/me/managed-accounts/{account_id}", response_model=ManagedAccountRead)
def update_account(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_user_with_manage_groups_perm),
    account_id: int,
    body: ManagedAccountUpdate,
):
    account = _require_owned_account(session, account_id, user.id)

    # If the caller is moving the account, the destination group must also be
    # owned by them.
    if body.managed_account_group_id is not None:
        _require_owned_group(session, body.managed_account_group_id, user.id)

    update_managed_account(
        session,
        account,
        display_name=body.display_name,
        managed_account_group_id=body.managed_account_group_id,
    )
    return _read_account(account, get_active_code_for_account(session, account.id))


@router.delete("/me/managed-accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_user_with_manage_groups_perm),
    account_id: int,
):
    account = _require_owned_account(session, account_id, user.id)
    soft_delete_user(session, account)


@router.post("/me/managed-accounts/{account_id}/reissue-code", response_model=ManagedAccountRead)
def reissue_code(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_user_with_manage_groups_perm),
    account_id: int,
):
    account = _require_owned_account(session, account_id, user.id)
    new_code = reissue_managed_account_code(session, account.id)
    return _read_account(account, new_code)


@router.post("/me/managed-accounts/{account_id}/open-as", response_model=UserTokenUpdate)
def open_as_account(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_user_with_manage_groups_perm),
    account_id: int,
):
    """Mint a JWT for one of my managed accounts. Owner JWT is the authorization;
    no code is required (the owner already controls the account)."""
    account = _require_owned_account(session, account_id, user.id)
    target = UserRead.model_validate(account)
    # Inherit premium from the owner (i.e. self) so the swapped session sees
    # the same entitlement the manager paid for.
    target.is_premium = is_premium_effective(session, account)
    return create_access_token(user, open_as_managed_account=target)


# ─── public picker ───


@router.get("/c/{share_token}", response_model=PublicPickerPayload)
def public_picker(
    *,
    request: Request,  # noqa: ARG001 — kept for parity with rate-limit-aware endpoints
    session: Session = Depends(get_session),
    share_token: str,
):
    """Anonymous: return a group's name and the list of names to pick from.
    Never includes owner data — anyone with the link can fetch this."""
    group = get_group_by_share_token(session, share_token)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    accounts = list_accounts_in_group(session, group.id)
    return PublicPickerPayload(
        group_name=group.name,
        members=[
            PublicPickerEntry(managed_account_id=a.id, display_name=a.display_name)
            for a in accounts
        ],
    )
