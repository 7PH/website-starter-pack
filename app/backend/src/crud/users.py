# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.user import UserBase


def get_user_by_email(session: Session, email: str) -> UserBase | None:
    """Retrieve a non-deleted user by their email."""
    return session.execute(
        select(UserBase).where(UserBase.email == email, UserBase.deleted_at.is_(None))
    ).scalar_one_or_none()


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


def delete_user(session: Session, user: UserBase) -> None:
    """Delete a user from the database."""
    session.delete(user)
    session.commit()


def is_email_taken(session: Session, email: str) -> bool:
    """Check if an email is already registered by a non-deleted user."""
    return (
        session.execute(
            select(UserBase).where(UserBase.email == email, UserBase.deleted_at.is_(None))
        ).scalar_one_or_none()
        is not None
    )


def get_user_by_stripe_id(session: Session, stripe_id: str) -> UserBase | None:
    """Retrieve a non-deleted user by their Stripe customer ID."""
    return session.execute(
        select(UserBase).where(UserBase.stripe_id == stripe_id, UserBase.deleted_at.is_(None))
    ).scalar_one_or_none()


def set_user_premium_status(session: Session, user: UserBase, is_premium: bool) -> None:
    """Update a user's premium status."""
    user.is_premium = is_premium
    session.commit()


def soft_delete_user(session: Session, user: UserBase) -> None:
    """Soft delete a user and anonymize their personal data.

    This sets deleted_at and anonymizes PII (email, name, password)
    while preserving the record for audit trail purposes.
    """
    user.deleted_at = datetime.now(UTC)
    user.email = f"deleted_{user.id}_{int(user.deleted_at.timestamp())}@deleted.local"
    user.first_name = "Deleted"
    user.last_name = "User"
    user.hashed_password = ""  # Invalidate password
    user.email_confirmed = False
    session.commit()
