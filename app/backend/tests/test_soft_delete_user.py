# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Deleting an account must stop its Stripe billing."""

from unittest.mock import MagicMock, patch

from src.crud import users as crud_users
from src.models.user import UserBase


def _user(stripe_id: str | None) -> UserBase:
    return UserBase(
        id=1,
        email="a@b.c",
        auth_method="password",
        stripe_id=stripe_id,
        is_premium=True,
        has_personal_subscription=True,
    )


def test_deletes_stripe_customer_and_clears_billing():
    user = _user("cus_123")
    with patch.object(crud_users, "delete_customer") as delete_customer:
        crud_users.soft_delete_user(MagicMock(), user)
    delete_customer.assert_called_once_with("cus_123")
    assert user.stripe_id is None
    assert user.is_premium is False
    assert user.has_personal_subscription is False
    assert user.deleted_at is not None


def test_skips_stripe_without_customer():
    user = _user(None)
    with patch.object(crud_users, "delete_customer") as delete_customer:
        crud_users.soft_delete_user(MagicMock(), user)
    delete_customer.assert_not_called()
    assert user.deleted_at is not None
