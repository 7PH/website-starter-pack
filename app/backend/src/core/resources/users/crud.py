from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import UserBase


def get_user_by_email(session: Session, email: str) -> UserBase | None:
    """Retrieve a user by their email."""
    return session.execute(
        select(UserBase).where(UserBase.email == email)
    ).scalar_one_or_none()


def create_user(session: Session, user: UserBase) -> None:
    """Add a new user to the database."""
    session.add(user)
    session.commit()


def get_user_by_id(session: Session, user_id: int) -> UserBase | None:
    """Retrieve a user by their ID."""
    return session.get(UserBase, user_id)


def update_user(session: Session, user: UserBase) -> None:
    """Commit changes to an existing user."""
    session.commit()


def is_email_taken(session: Session, email: str) -> bool:
    """Check if an email is already registered in the database."""
    return (
        session.execute(
            select(UserBase).where(UserBase.email == email)
        ).scalar_one_or_none()
        is not None
    )


def set_password_reset_token(session: Session, user: UserBase, token: str) -> None:
    """Set a password reset token for a user."""
    user.password_reset_token = token
    session.commit()


def reset_password(session: Session, user: UserBase, new_password: str) -> None:
    """Reset a user's password and clear their reset token."""
    user.hashed_password = new_password
    user.password_reset_token = None
    session.commit()
