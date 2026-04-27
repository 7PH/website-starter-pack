# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Tests for managed-account permission guards and premium inheritance."""

import os

os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")
os.environ.setdefault("TOKEN_HASH_SECRET", "test-secret-not-for-prod")

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from src.helpers.auth import get_current_nonmanaged_user, is_premium_effective
from src.models.managed_account_group import ManagedAccountGroupBase
from src.models.user import UserBase
from src.schemas.user import UserRead


def _user_read(auth_method: str = "password", **overrides) -> UserRead:
    base = dict(
        id=1,
        email="user@example.com" if auth_method != "access_code" else None,
        first_name="Sam",
        last_name="Doe",
        is_admin=False,
        is_premium=False,
        auth_method=auth_method,
    )
    base.update(overrides)
    return UserRead(**base)


def _user_db(
    user_id: int = 1,
    auth_method: str = "password",
    is_premium: bool = False,
    managed_account_group_id: int | None = None,
    deleted_at=None,
) -> UserBase:
    u = UserBase()
    u.id = user_id
    u.email = None if auth_method == "access_code" else f"u{user_id}@example.com"
    u.first_name = "First"
    u.last_name = "Last"
    u.display_name = None
    u.is_admin = False
    u.is_premium = is_premium
    u.has_personal_subscription = False
    u.auth_method = auth_method
    u.managed_account_group_id = managed_account_group_id
    u.deleted_at = deleted_at
    u.custom_data = {}
    return u


def _group(group_id: int = 10, owner_id: int = 1) -> ManagedAccountGroupBase:
    g = ManagedAccountGroupBase()
    g.id = group_id
    g.owner_id = owner_id
    g.name = "Math 101"
    g.share_token = "abc123"
    g.created_at = datetime.now(UTC)
    g.archived_at = None
    return g


class TestGetCurrentNonmanagedUser:
    @pytest.mark.asyncio
    async def test_passes_through_password_user(self):
        u = _user_read(auth_method="password")
        result = await get_current_nonmanaged_user(u)
        assert result is u

    @pytest.mark.asyncio
    async def test_passes_through_oauth_user(self):
        u = _user_read(auth_method="oauth")
        result = await get_current_nonmanaged_user(u)
        assert result is u

    @pytest.mark.asyncio
    async def test_blocks_access_code_user(self):
        u = _user_read(auth_method="access_code", email=None)
        with pytest.raises(HTTPException) as exc:
            await get_current_nonmanaged_user(u)
        assert exc.value.status_code == 403


class TestIsPremiumEffective:
    def test_password_premium_user_returns_own_flag(self):
        session = MagicMock()
        u = _user_db(auth_method="password", is_premium=True)
        assert is_premium_effective(session, u) is True
        # No DB lookups for the manager — non-managed users short-circuit.
        session.get.assert_not_called()

    def test_password_free_user_returns_own_flag(self):
        session = MagicMock()
        u = _user_db(auth_method="password", is_premium=False)
        assert is_premium_effective(session, u) is False

    def test_managed_account_inherits_owner_premium(self):
        """Owner is premium → managed account is effectively premium."""
        owner = _user_db(user_id=1, auth_method="password", is_premium=True)
        managed = _user_db(
            user_id=42,
            auth_method="access_code",
            is_premium=False,
            managed_account_group_id=10,
        )
        group = _group(group_id=10, owner_id=1)

        session = MagicMock()
        session.get.side_effect = lambda model, key: {
            (ManagedAccountGroupBase, 10): group,
            (UserBase, 1): owner,
        }.get((model, key))

        assert is_premium_effective(session, managed) is True

    def test_managed_account_inherits_owner_non_premium(self):
        """Owner is free → managed account is also free."""
        owner = _user_db(user_id=1, auth_method="password", is_premium=False)
        managed = _user_db(
            user_id=42,
            auth_method="access_code",
            is_premium=False,
            managed_account_group_id=10,
        )
        group = _group(group_id=10, owner_id=1)

        session = MagicMock()
        session.get.side_effect = lambda model, key: {
            (ManagedAccountGroupBase, 10): group,
            (UserBase, 1): owner,
        }.get((model, key))

        assert is_premium_effective(session, managed) is False

    def test_managed_account_with_deleted_owner_returns_false(self):
        """Edge: the owner row was soft-deleted. Don't grant premium off a tombstone."""
        owner = _user_db(
            user_id=1,
            auth_method="deleted",
            is_premium=True,  # legacy row may still have True — irrelevant once deleted
            deleted_at=datetime.now(UTC),
        )
        managed = _user_db(
            user_id=42,
            auth_method="access_code",
            managed_account_group_id=10,
        )
        group = _group(group_id=10, owner_id=1)

        session = MagicMock()
        session.get.side_effect = lambda model, key: {
            (ManagedAccountGroupBase, 10): group,
            (UserBase, 1): owner,
        }.get((model, key))

        assert is_premium_effective(session, managed) is False

    def test_managed_account_with_missing_group_returns_false(self):
        """Edge: group FK row is gone (shouldn't happen with CASCADE, but guard it)."""
        managed = _user_db(
            user_id=42,
            auth_method="access_code",
            managed_account_group_id=10,
        )
        session = MagicMock()
        session.get.return_value = None

        assert is_premium_effective(session, managed) is False

    def test_access_code_user_without_group_returns_own_flag(self):
        """Defensive: an access_code user with no group_id falls back to own flag."""
        managed = _user_db(
            user_id=42,
            auth_method="access_code",
            is_premium=False,
            managed_account_group_id=None,
        )
        session = MagicMock()
        assert is_premium_effective(session, managed) is False
        session.get.assert_not_called()
