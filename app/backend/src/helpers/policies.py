# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Pluggable authorization policies.

The starterpack ships defaults; sub-apps override at startup from main_ext.py
to gate features by tier, role, etc. Pattern mirrors `register_code_validator`
in helpers/auth.py — one slot per policy, replacement is explicit.
"""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from ..schemas.user import UserRead
from .auth import get_current_user

GroupManagementPolicy = Callable[[UserRead], bool]


# Default: any signed-in user can create/manage groups. Apps that want to gate
# this on premium tier (or anything else) call set_group_management_policy().
def _default_policy(_user: UserRead) -> bool:
    return True


_group_management_policy: GroupManagementPolicy = _default_policy


def set_group_management_policy(fn: GroupManagementPolicy) -> None:
    """Override who can create/manage managed account groups.

    Sub-apps call this from main_ext.py at import time, e.g.

        def can_manage(u): return u.is_premium and u.subscription_tier == "pro"
        set_group_management_policy(can_manage)
    """
    global _group_management_policy
    _group_management_policy = fn


def get_group_management_policy() -> GroupManagementPolicy:
    return _group_management_policy


async def can_manage_groups(user: UserRead = Depends(get_current_user)) -> UserRead:
    """FastAPI dependency: 403 if the registered policy rejects this user.

    Managed accounts are always rejected, regardless of the registered policy
    — a managed account cannot in turn manage other managed accounts.
    """
    if user.auth_method == "access_code":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Managed accounts cannot manage groups.",
        )
    if not _group_management_policy(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage groups",
        )
    return user


def _reset_group_management_policy_for_tests() -> None:
    """Test-only helper. Do not call from production code."""
    global _group_management_policy
    _group_management_policy = _default_policy
