# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Pluggable authorization policies.

Group-management policy is driven by the typed event bus
(``GroupManagementCheck`` in ``helpers/hooks.py``). Sub-apps register a
handler from ``main_ext.py``::

    @on(GroupManagementCheck)
    def my_policy(session: Session, event: GroupManagementCheck) -> None:
        if not is_teacher(session, event.user):
            event.allow = False
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..schemas.user import UserRead
from .auth import get_current_user
from .db import get_session
from .hooks import GroupManagementCheck, fire


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
