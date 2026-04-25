# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Account-related guards used from controllers."""

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..crud.users import get_user_by_id


def assert_min_account_age(session: Session, user_id: int, min_minutes: int = 10) -> None:
    """Reject requests from accounts created less than ``min_minutes`` ago.

    Blocks signup-and-spam scripts that race through registration then hammer a
    rate-limited endpoint from the fresh account.
    """
    user = get_user_by_id(session, user_id)
    if user is None or user.created_at is None:
        return
    if datetime.now(UTC) - user.created_at < timedelta(minutes=min_minutes):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account too new — try again in a few minutes.",
        )
