# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""CRUD for access codes — the default backing for sign-in by code.

Apps that want fancier semantics (paired teacher+student codes, single-use,
context-bound, ...) ignore this module and register their own
`@on(AccessCodeResolution)` handler in `main_ext.py`.
"""

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.access_code import AccessCodeBase
from ..models.user import UserBase

# Crockford base32, no I/L/O/U — each char = 5 bits.
# Default length 5 = 25 bits of entropy. That's small in absolute terms, but
# /auth/code lookups are scoped to a specific managed_account_id and each
# (ip, account_id) bucket is rate-limited to 5 failures per 15 min, so the
# effective brute-force ceiling is far below this entropy.
_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def generate_code(length: int = 5) -> str:
    return "".join(secrets.choice(_CROCKFORD) for _ in range(length))


def issue_code(
    session: Session,
    user_id: int,
    *,
    expires_in: timedelta | None = None,
    length: int = 5,
) -> AccessCodeBase:
    """Mint a new code for the user and persist it."""
    code = AccessCodeBase(
        code=generate_code(length),
        user_id=user_id,
        expires_at=(datetime.now(UTC) + expires_in) if expires_in else None,
    )
    session.add(code)
    session.commit()
    session.refresh(code)
    return code


def resolve_code(session: Session, user_id: int, code: str) -> UserBase | None:
    """Look up a code scoped to the given managed-account ``user_id``. Returns
    the user row when the code is active and not expired, else ``None``.

    Scoping by ``user_id`` is what allows two different managers to issue the
    same code string to their own students without collision.
    """
    now = datetime.now(UTC)
    row = session.execute(
        select(AccessCodeBase, UserBase)
        .join(UserBase, UserBase.id == AccessCodeBase.user_id)
        .where(
            AccessCodeBase.user_id == user_id,
            AccessCodeBase.code == code,
            AccessCodeBase.revoked_at.is_(None),
            (AccessCodeBase.expires_at.is_(None)) | (AccessCodeBase.expires_at > now),
            UserBase.deleted_at.is_(None),
        )
    ).first()
    return row[1] if row else None
