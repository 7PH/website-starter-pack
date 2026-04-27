# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Default access-code validator.

Wired by sub-apps in main_ext.py via:

    from .helpers.auth import register_code_validator
    from .helpers.access_codes import default_access_code_validator
    register_code_validator(default_access_code_validator)

The validator signature is (managed_account_id, code, request); apps with
custom semantics (paired teacher+student tokens, single-use codes, ...)
write their own with the same signature.
"""

from fastapi import Request

from ..crud.access_codes import resolve_code as crud_resolve_code
from ..helpers.db import SessionLocal
from ..models.user import UserBase


def default_access_code_validator(
    managed_account_id: int,
    code: str,
    request: Request,  # noqa: ARG001
) -> UserBase | None:
    """Look up the ``(managed_account_id, code)`` pair in the access_codes
    table and return the bound user, or ``None`` when no active code matches.

    Codes are unique per managed account (PK is composite), so two different
    managers' students can share a code string — the lookup scopes correctly.
    """
    with SessionLocal() as session:
        user = crud_resolve_code(session, managed_account_id, code)
        if user is None:
            return None
        session.expunge(user)
        return user
