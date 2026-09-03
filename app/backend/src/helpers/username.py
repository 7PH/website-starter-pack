# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Username validation and normalization.

The charset excludes '@' so a username can never collide with an email in the
login box, and stays URL-safe since handles tend to end up in paths.
"""

import re
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

USERNAME_MIN_LENGTH = 2
USERNAME_MAX_LENGTH = 32

# Brackets are safe here: Postgres LIKE treats them as literals (that's SQL
# Server syntax), and percent-encoding handles them in a URL. The '-' stays
# last so it can't open a character range. Keep '$' rather than '\Z' even
# though '$' also matches before a trailing newline: validate_username()
# strips first, and this pattern ships to the browser, where '\Z' would mean
# a literal "Z".
USERNAME_PATTERN = re.compile(rf"^[a-zA-Z0-9_\[\]-]{{{USERNAME_MIN_LENGTH},{USERNAME_MAX_LENGTH}}}$")


class UsernameError(ValueError):
    """Raised when a username fails validation."""


def normalize_username(value: str) -> str:
    """Trim surrounding whitespace. Case is preserved for display."""
    return value.strip()


def validate_username(value: str) -> str:
    """Return the normalized username, or raise UsernameError.

    Case is preserved for display; uniqueness is case-insensitive.
    """
    username = normalize_username(value)
    if not USERNAME_PATTERN.match(username):
        raise UsernameError("invalid")
    return username


@contextmanager
def username_conflict_as_409(session: Session) -> Iterator[None]:
    """Turn a lost race on the unique index into the 409 the pre-check intends.

    Checking then writing is racy: concurrent signups on the same handle both
    pass the check, and the loser would otherwise get a 500.
    """
    try:
        yield
    except IntegrityError as exc:
        if "idx_users_username_lower" not in str(exc.orig):
            raise
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken") from exc
