# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Default access-code resolver.

Wired by sub-apps in ``main_ext.py``::

    from .helpers.access_codes import register_default_access_code_resolver
    register_default_access_code_resolver()

Apps with custom semantics (paired teacher+student tokens, single-use codes,
...) skip this and register their own handler::

    from .helpers.hooks import AccessCodeResolution, on

    @on(AccessCodeResolution)
    def my_resolver(session, event):
        if event.user is None:
            event.user = my_lookup(...)
"""

from sqlalchemy.orm import Session

from ..crud.access_codes import resolve_code as crud_resolve_code
from ..helpers.db import SessionLocal
from .hooks import AccessCodeResolution, on


def register_default_access_code_resolver() -> None:
    """Register the default access-code resolver as a hook handler.

    Looks up the ``(managed_account_id, code)`` pair in the access_codes
    table and binds ``event.user`` to the resolved row. Codes are unique
    per managed account (PK is composite), so two different managers'
    students can share a code string — the lookup scopes correctly.
    """

    @on(AccessCodeResolution)
    def _default_resolver(_session: Session, event: AccessCodeResolution) -> None:
        if event.user is not None:
            return
        # Use a fresh session: the resolver may be called outside the
        # request scope in some test paths, and we want the read to be
        # isolated from the controller's session lifecycle.
        with SessionLocal() as session:
            user = crud_resolve_code(session, event.managed_account_id, event.code)
            if user is None:
                return
            session.expunge(user)
            event.user = user
