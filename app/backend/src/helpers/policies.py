# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Pluggable authorization policies.

Group-management policy is now driven by the typed event bus
(``GroupManagementCheck`` in ``helpers/hooks.py``). Sub-apps register a
handler from ``main_ext.py``::

    @on(GroupManagementCheck)
    def my_policy(session: Session, event: GroupManagementCheck) -> None:
        if not is_teacher(session, event.user):
            event.allow = False

The legacy ``set_group_management_policy(fn)`` API is kept as a
deprecated shim for one release. New code should use ``@on(...)``.
"""

import warnings
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..schemas.user import UserRead
from .auth import get_current_user
from .db import get_session
from .hooks import GroupManagementCheck, fire, on

GroupManagementPolicy = Callable[[UserRead], bool]


def set_group_management_policy(fn: GroupManagementPolicy) -> None:
    """**Deprecated.** Use ``@on(GroupManagementCheck)`` instead.

    Registers ``fn`` as a handler that flips ``event.allow`` to False
    when ``fn(user)`` returns False. Kept for backwards compatibility
    with sub-apps that haven't migrated yet; will be removed in v3.5.0.
    """
    warnings.warn(
        "set_group_management_policy is deprecated; use @on(GroupManagementCheck) "
        "from helpers/hooks.py instead. Will be removed in v3.5.0.",
        DeprecationWarning,
        stacklevel=2,
    )

    @on(GroupManagementCheck)
    def _shim(_session: Session, event: GroupManagementCheck) -> None:
        if not fn(event.user):
            event.allow = False


def _reset_group_management_policy_for_tests() -> None:
    """Test-only helper. Clears every registered hook handler. Do not call from production code."""
    from .hooks import _reset_hooks_for_tests

    _reset_hooks_for_tests()


async def get_user_with_manage_groups_perm(
    user: UserRead = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> UserRead:
    """FastAPI dependency: 403 if any registered handler denies the user.

    Managed accounts are always rejected — a managed account cannot in turn
    manage other managed accounts. The check happens before the event fires,
    so handlers don't need to special-case ``auth_method == 'access_code'``.
    """
    if user.auth_method == "access_code":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Managed accounts cannot manage groups.",
        )
    event = fire(session, GroupManagementCheck(user=user))
    if not event.allow:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage groups",
        )
    return user
