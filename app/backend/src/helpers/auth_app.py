# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
"""Project-specific auth hooks. Customize as needed."""

from sqlalchemy.orm import Session

from ..models.user import UserBase


def pre_login(session: Session, user: UserBase, password: str) -> bool | None:
    """
    Called during login before the standard bcrypt password check.

    Return values:
      True  — user is authenticated (skip standard check)
      False — reject the login immediately
      None  — proceed with standard bcrypt check
    """
    return None
