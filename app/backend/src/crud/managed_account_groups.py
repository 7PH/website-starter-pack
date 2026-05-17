# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""CRUD for managed account groups and the managed accounts inside them.

A managed account is a `users` row with auth_method='access_code' and a
non-null managed_account_group_id; functions here keep that invariant.
"""

import secrets
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from ..models.access_code import AccessCodeBase
from ..models.managed_account_group import ManagedAccountGroupBase
from ..models.user import UserBase
from .access_codes import issue_code

# 22 chars of token_urlsafe ≈ 130 bits — plenty for a public picker URL.
_SHARE_TOKEN_LENGTH = 22


def _generate_share_token() -> str:
    return secrets.token_urlsafe(_SHARE_TOKEN_LENGTH)[:_SHARE_TOKEN_LENGTH]


# ─── group ops ───


def create_group(session: Session, owner_id: int, name: str) -> ManagedAccountGroupBase:
    group = ManagedAccountGroupBase(
        owner_id=owner_id,
        name=name,
        share_token=_generate_share_token(),
    )
    session.add(group)
    session.commit()
    session.refresh(group)
    return group


def get_group(session: Session, group_id: int) -> ManagedAccountGroupBase | None:
    return session.get(ManagedAccountGroupBase, group_id)


def get_group_by_share_token(session: Session, share_token: str) -> ManagedAccountGroupBase | None:
    return session.execute(
        select(ManagedAccountGroupBase).where(
            ManagedAccountGroupBase.share_token == share_token,
            ManagedAccountGroupBase.archived_at.is_(None),
        )
    ).scalar_one_or_none()


def list_groups_for_owner(session: Session, owner_id: int) -> list[ManagedAccountGroupBase]:
    return list(
        session.execute(
            select(ManagedAccountGroupBase)
            .where(ManagedAccountGroupBase.owner_id == owner_id)
            .order_by(ManagedAccountGroupBase.created_at.desc())
        ).scalars()
    )


def count_groups_for_owner(session: Session, owner_id: int) -> int:
    return (
        session.execute(
            select(func.count())
            .select_from(ManagedAccountGroupBase)
            .where(
                ManagedAccountGroupBase.owner_id == owner_id,
                ManagedAccountGroupBase.archived_at.is_(None),
            )
        ).scalar()
        or 0
    )


def update_group(
    session: Session,
    group: ManagedAccountGroupBase,
    *,
    name: str | None = None,
    archived: bool | None = None,
) -> ManagedAccountGroupBase:
    if name is not None:
        group.name = name
    if archived is not None:
        group.archived_at = datetime.now(UTC) if archived else None
    session.commit()
    session.refresh(group)
    return group


def delete_group(session: Session, group: ManagedAccountGroupBase) -> None:
    """Hard-delete the group. The FK cascade removes all managed-account user rows."""
    session.delete(group)
    session.commit()


def rotate_share_token(session: Session, group: ManagedAccountGroupBase) -> ManagedAccountGroupBase:
    group.share_token = _generate_share_token()
    session.commit()
    session.refresh(group)
    return group


# ─── managed account (user-row) ops ───


def list_accounts_in_group(session: Session, group_id: int) -> list[UserBase]:
    return list(
        session.execute(
            select(UserBase)
            .where(
                UserBase.managed_account_group_id == group_id,
                UserBase.deleted_at.is_(None),
            )
            .order_by(UserBase.created_at.asc())
        ).scalars()
    )


def count_accounts_in_group(session: Session, group_id: int) -> int:
    return (
        session.execute(
            select(func.count())
            .select_from(UserBase)
            .where(
                UserBase.managed_account_group_id == group_id,
                UserBase.deleted_at.is_(None),
            )
        ).scalar()
        or 0
    )


def count_accounts_for_owner(session: Session, owner_id: int) -> int:
    """Count total managed accounts across all groups owned by ``owner_id``."""
    return (
        session.execute(
            select(func.count(UserBase.id))
            .join(ManagedAccountGroupBase, ManagedAccountGroupBase.id == UserBase.managed_account_group_id)
            .where(
                ManagedAccountGroupBase.owner_id == owner_id,
                UserBase.deleted_at.is_(None),
            )
        ).scalar()
        or 0
    )


def get_managed_account(session: Session, user_id: int) -> UserBase | None:
    """Get a managed account by id. Returns None if the user isn't a managed account."""
    user = session.get(UserBase, user_id)
    if (
        user is None
        or user.deleted_at is not None
        or user.auth_method != "access_code"
        or user.managed_account_group_id is None
    ):
        return None
    return user


def create_managed_account(
    session: Session,
    *,
    group_id: int,
    display_name: str,
) -> tuple[UserBase, str]:
    """Create a managed-account user row in `group_id` and mint its first code.

    Returns (user, plaintext_code). The caller shows the code to the owner once;
    after that they fetch it from `access_codes` joined to user_id.
    """
    user = UserBase(
        auth_method="access_code",
        display_name=display_name,
        managed_account_group_id=group_id,
        # email / hashed_password / oauth_* all NULL — enforced by users_auth_integrity.
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    code = issue_code(session, user.id)
    return user, code.code


def bulk_create_managed_accounts(
    session: Session,
    *,
    group_id: int,
    display_names: list[str],
) -> tuple[list[tuple[UserBase, str]], int]:
    """Create many managed accounts in one go, deduping case-insensitively.

    Returns ``(created, skipped_count)`` where each entry of ``created`` is the
    user row paired with its freshly-minted access code. Duplicates are silently
    skipped:
      - within the input batch itself (e.g. two rows with the same name), and
      - against display_names that already exist in the group.

    Whitespace-only or empty names are dropped. The caller is responsible for
    enforcing the per-group quota.
    """
    existing = {
        (n or "").strip().lower()
        for n in session.execute(
            select(UserBase.display_name).where(
                UserBase.managed_account_group_id == group_id,
                UserBase.deleted_at.is_(None),
            )
        ).scalars()
        if n
    }

    created: list[tuple[UserBase, str]] = []
    seen: set[str] = set()
    skipped = 0

    for name in display_names:
        cleaned = (name or "").strip()
        if not cleaned:
            skipped += 1
            continue
        key = cleaned.lower()
        if key in seen or key in existing:
            skipped += 1
            continue
        seen.add(key)
        user, code = create_managed_account(session, group_id=group_id, display_name=cleaned)
        created.append((user, code))

    return created, skipped


def update_managed_account(
    session: Session,
    user: UserBase,
    *,
    display_name: str | None = None,
    managed_account_group_id: int | None = None,
) -> UserBase:
    if display_name is not None:
        user.display_name = display_name
    if managed_account_group_id is not None:
        user.managed_account_group_id = managed_account_group_id
    session.commit()
    session.refresh(user)
    return user


def reissue_managed_account_code(session: Session, user_id: int) -> str:
    """Revoke any active codes on this managed account and mint a new one.

    Single transaction so a failed insert leaves the prior codes intact.
    `issue_code` does the final commit.
    """
    now = datetime.now(UTC)
    session.execute(
        update(AccessCodeBase)
        .where(
            AccessCodeBase.user_id == user_id,
            AccessCodeBase.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    new_code = issue_code(session, user_id)
    return new_code.code


def get_active_code_for_account(session: Session, user_id: int) -> str | None:
    """Return the most recent non-revoked, non-expired code for a managed account."""
    now = datetime.now(UTC)
    row = session.execute(
        select(AccessCodeBase)
        .where(
            AccessCodeBase.user_id == user_id,
            AccessCodeBase.revoked_at.is_(None),
            (AccessCodeBase.expires_at.is_(None)) | (AccessCodeBase.expires_at > now),
        )
        .order_by(AccessCodeBase.created_at.desc())
    ).scalar_one_or_none()
    return row.code if row else None


def get_active_codes_for_accounts(session: Session, user_ids: list[int]) -> dict[int, str]:
    """Return ``{user_id: latest_active_code}`` in a single query.

    Postgres DISTINCT ON picks the newest non-revoked, non-expired code per
    user. Users with no active code are absent from the result (callers use
    ``dict.get``). Replaces an N+1 over `get_active_code_for_account`.
    """
    if not user_ids:
        return {}
    now = datetime.now(UTC)
    rows = session.execute(
        select(AccessCodeBase)
        .where(
            AccessCodeBase.user_id.in_(user_ids),
            AccessCodeBase.revoked_at.is_(None),
            (AccessCodeBase.expires_at.is_(None)) | (AccessCodeBase.expires_at > now),
        )
        .order_by(AccessCodeBase.user_id, AccessCodeBase.created_at.desc())
        .distinct(AccessCodeBase.user_id)
    ).scalars().all()
    return {row.user_id: row.code for row in rows}
