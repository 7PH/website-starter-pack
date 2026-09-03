# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.organization import UserOrganizationBase
from ..models.user import UserBase


def get_user_by_email(session: Session, email: str) -> UserBase | None:
    """Retrieve a non-deleted user by their email."""
    return session.execute(
        select(UserBase).where(UserBase.email == email, UserBase.deleted_at.is_(None))
    ).scalar_one_or_none()


def get_user_by_username(session: Session, username: str) -> UserBase | None:
    """Retrieve a non-deleted user by username, case-insensitively."""
    return session.execute(
        select(UserBase).where(
            func.lower(UserBase.username) == username.lower(),
            UserBase.deleted_at.is_(None),
        )
    ).scalar_one_or_none()


def is_username_taken(session: Session, username: str, exclude_user_id: int | None = None) -> bool:
    """Check if a username is already held by a non-deleted user.

    `exclude_user_id` lets a rename re-submit the user's current handle (or a
    case variant of it) without tripping on their own row.
    """
    existing = get_user_by_username(session, username)
    return existing is not None and existing.id != exclude_user_id


def create_user(session: Session, user: UserBase) -> None:
    """Add a new user to the database."""
    session.add(user)
    session.commit()


def get_user_by_id(session: Session, user_id: int, include_deleted: bool = False) -> UserBase | None:
    """Retrieve a user by their ID. By default excludes deleted users."""
    user = session.get(UserBase, user_id)
    if user and not include_deleted and user.deleted_at is not None:
        return None
    return user


def update_user(session: Session, user: UserBase) -> None:
    """Commit changes to an existing user."""
    session.commit()


def is_email_taken(session: Session, email: str) -> bool:
    """Check if an email is already registered by a non-deleted user."""
    return get_user_by_email(session, email) is not None


def get_user_by_stripe_id(session: Session, stripe_id: str) -> UserBase | None:
    """Retrieve a non-deleted user by their Stripe customer ID."""
    return session.execute(
        select(UserBase).where(UserBase.stripe_id == stripe_id, UserBase.deleted_at.is_(None))
    ).scalar_one_or_none()


def update_user_premium_cache(session: Session, user_id: int) -> None:
    """Recalculate is_premium from actual sources (personal subscription and org seats).

    This should be called after any change to has_personal_subscription or has_premium_seat.
    """
    user = get_user_by_id(session, user_id)
    if not user:
        return

    has_org_seat = (
        session.execute(
            select(UserOrganizationBase).where(
                UserOrganizationBase.user_id == user_id,
                UserOrganizationBase.has_premium_seat.is_(True),
            )
        ).scalar_one_or_none()
        is not None
    )

    user.is_premium = user.has_personal_subscription or has_org_seat
    session.commit()


def soft_delete_user(session: Session, user: UserBase) -> None:
    """Soft delete a user and anonymize their personal data.

    Sets deleted_at, switches auth_method to the 'deleted' sentinel, and clears
    every PII column. The record is preserved for audit trail / FK integrity.
    The 'deleted' branch of users_auth_integrity has no column requirements,
    so nulling everything is accepted by the CHECK constraint.
    """
    user.deleted_at = datetime.now(UTC)
    user.auth_method = "deleted"
    user.email = None
    user.first_name = None
    user.last_name = None
    user.display_name = None
    # Freeing the handle is safe: with every label column NULL the user renders
    # as "Deleted user", so old content is never re-attributed to a new owner.
    user.username = None
    user.hashed_password = None
    user.oauth_provider = None
    user.oauth_id = None
    user.email_confirmed = False
    session.commit()
