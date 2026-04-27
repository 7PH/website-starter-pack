# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Tests for the managed account groups controller and permission policy."""

import os

os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")
os.environ.setdefault("TOKEN_HASH_SECRET", "test-secret-not-for-prod")

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.controllers.managed_account_groups import (
    _require_owned_account,
    _require_owned_group,
    bulk_create_accounts,
    open_as_account,
)
from src.crud import managed_account_groups as crud
from src.helpers import policies
from src.models.managed_account_group import ManagedAccountGroupBase
from src.models.user import UserBase
from src.schemas.managed_account import ManagedAccountBulkCreate, ManagedAccountCreate
from src.schemas.user import UserRead


@pytest.fixture
def reset_policy():
    policies._reset_group_management_policy_for_tests()
    yield
    policies._reset_group_management_policy_for_tests()


def _owner(user_id: int = 1) -> UserRead:
    return UserRead(
        id=user_id,
        email=f"owner{user_id}@example.com",
        first_name="Own",
        last_name="Er",
        is_admin=False,
        is_premium=False,
        auth_method="password",
    )


def _group(group_id: int = 10, owner_id: int = 1) -> ManagedAccountGroupBase:
    g = ManagedAccountGroupBase()
    g.id = group_id
    g.owner_id = owner_id
    g.name = "Math 101"
    g.share_token = "abc123"
    g.created_at = datetime.now(UTC)
    g.archived_at = None
    return g


def _account(user_id: int = 100, group_id: int = 10) -> UserBase:
    u = UserBase()
    u.id = user_id
    u.email = None
    u.first_name = None
    u.last_name = None
    u.display_name = "Alice"
    u.is_admin = False
    u.is_premium = False
    u.auth_method = "access_code"
    u.managed_account_group_id = group_id
    u.deleted_at = None
    u.has_personal_subscription = False
    u.custom_data = {}
    u.created_at = datetime.now(UTC)
    return u


class TestPolicy:
    @pytest.mark.asyncio
    async def test_default_policy_allows_any_user(self, reset_policy):
        result = await policies.can_manage_groups(_owner())
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_override_policy_can_block(self, reset_policy):
        policies.set_group_management_policy(lambda u: u.is_premium)
        with pytest.raises(HTTPException) as exc:
            await policies.can_manage_groups(_owner())
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_override_policy_can_allow_premium(self, reset_policy):
        policies.set_group_management_policy(lambda u: u.is_premium)
        u = _owner()
        u.is_premium = True
        result = await policies.can_manage_groups(u)
        assert result.is_premium is True


class TestOwnership:
    def test_require_owned_group_404_when_missing(self):
        session = MagicMock()
        with patch(
            "src.controllers.managed_account_groups.get_group", return_value=None
        ), pytest.raises(HTTPException) as exc:
            _require_owned_group(session, group_id=999, user_id=1)
        assert exc.value.status_code == 404

    def test_require_owned_group_404_when_other_owner(self):
        """Don't leak existence — return 404 for groups owned by someone else."""
        session = MagicMock()
        other_group = _group(owner_id=2)
        with patch(
            "src.controllers.managed_account_groups.get_group", return_value=other_group
        ), pytest.raises(HTTPException) as exc:
            _require_owned_group(session, group_id=10, user_id=1)
        assert exc.value.status_code == 404

    def test_require_owned_group_returns_when_owner_matches(self):
        session = MagicMock()
        g = _group(owner_id=1)
        with patch("src.controllers.managed_account_groups.get_group", return_value=g):
            result = _require_owned_group(session, group_id=10, user_id=1)
        assert result is g

    def test_require_owned_account_404_when_other_owner(self):
        """Account exists but its group belongs to a different owner."""
        session = MagicMock()
        account = _account(group_id=10)
        other_group = _group(group_id=10, owner_id=2)
        with (
            patch("src.controllers.managed_account_groups.get_managed_account", return_value=account),
            patch("src.controllers.managed_account_groups.get_group", return_value=other_group),
            pytest.raises(HTTPException) as exc,
        ):
            _require_owned_account(session, account_id=100, user_id=1)
        assert exc.value.status_code == 404

    def test_require_owned_account_404_when_not_managed(self):
        """get_managed_account returns None for non-managed users."""
        session = MagicMock()
        with patch(
            "src.controllers.managed_account_groups.get_managed_account", return_value=None
        ), pytest.raises(HTTPException) as exc:
            _require_owned_account(session, account_id=100, user_id=1)
        assert exc.value.status_code == 404


class TestOpenAs:
    def test_open_as_mints_token_with_parent_user_id(self):
        """The owner-initiated 'open as' flow stamps parent_user_id in the JWT."""
        session = MagicMock()
        owner = _owner(user_id=1)
        account = _account(user_id=100, group_id=10)
        owner_group = _group(group_id=10, owner_id=1)

        with (
            patch("src.controllers.managed_account_groups.get_managed_account", return_value=account),
            patch("src.controllers.managed_account_groups.get_group", return_value=owner_group),
        ):
            result = open_as_account(session=session, user=owner, account_id=100)

        assert result.access_token
        assert result.user.id == 100
        assert result.user.auth_method == "access_code"
        assert result.token_parsed.real_admin_id is None  # not an admin impersonation


def _mock_existing_names(session: MagicMock, names: list[str]) -> None:
    """Make session.execute(...).scalars() return `names` once, then []. The
    CRUD only queries existing names in this group once at the top, so a
    single-shot iterator is enough."""
    scalars_mock = MagicMock()
    scalars_mock.__iter__ = lambda self: iter(names)
    execute_mock = MagicMock()
    execute_mock.scalars.return_value = scalars_mock
    session.execute.return_value = execute_mock


class TestBulkCreateCrud:
    """Unit tests for crud.bulk_create_managed_accounts (the dedup logic)."""

    def test_creates_unique_names_with_codes(self):
        session = MagicMock()
        _mock_existing_names(session, [])

        with patch.object(
            crud,
            "create_managed_account",
            side_effect=[(_account(1), "CODE1"), (_account(2), "CODE2")],
        ) as mock_create:
            created, skipped = crud.bulk_create_managed_accounts(
                session, group_id=10, display_names=["Alice", "Bob"]
            )

        assert len(created) == 2
        assert skipped == 0
        assert mock_create.call_count == 2

    def test_dedupes_within_batch_case_insensitive(self):
        session = MagicMock()
        _mock_existing_names(session, [])

        with patch.object(crud, "create_managed_account", return_value=(_account(1), "X")) as mock_create:
            created, skipped = crud.bulk_create_managed_accounts(
                session, group_id=10, display_names=["Alice", "alice", "ALICE"]
            )

        assert len(created) == 1
        assert skipped == 2
        assert mock_create.call_count == 1

    def test_dedupes_against_existing(self):
        """Names already present in the group are silently skipped."""
        session = MagicMock()
        _mock_existing_names(session, ["Alice"])  # already in group

        with patch.object(crud, "create_managed_account", return_value=(_account(2), "Y")) as mock_create:
            created, skipped = crud.bulk_create_managed_accounts(
                session, group_id=10, display_names=["alice", "Bob"]
            )

        assert len(created) == 1
        assert skipped == 1
        # Confirm only Bob was created (Alice was deduped against existing).
        assert mock_create.call_args.kwargs["display_name"] == "Bob"

    def test_skips_blank_strings(self):
        session = MagicMock()
        _mock_existing_names(session, [])

        with patch.object(crud, "create_managed_account", return_value=(_account(1), "X")):
            created, skipped = crud.bulk_create_managed_accounts(
                session, group_id=10, display_names=["", "   ", "Alice"]
            )

        assert len(created) == 1
        assert skipped == 2


class TestBulkCreateController:
    def test_quota_exceeded_returns_400(self):
        """current + len(body) > MAX → 400 before any rows are touched."""
        session = MagicMock()
        owner = _owner()
        owner_group = _group(owner_id=1)

        with (
            patch("src.controllers.managed_account_groups.get_group", return_value=owner_group),
            patch("src.controllers.managed_account_groups.count_accounts_for_owner", return_value=999),
            patch("src.controllers.managed_account_groups.MANAGED_ACCOUNTS_MAX_PER_USER", 1000),
            pytest.raises(HTTPException) as exc,
        ):
            bulk_create_accounts(
                session=session,
                user=owner,
                group_id=10,
                body=ManagedAccountBulkCreate(
                    accounts=[ManagedAccountCreate(display_name="Alice"), ManagedAccountCreate(display_name="Bob")]
                ),
            )

        assert exc.value.status_code == 400

    def test_within_quota_calls_crud_and_returns_response(self):
        session = MagicMock()
        owner = _owner()
        owner_group = _group(owner_id=1)

        with (
            patch("src.controllers.managed_account_groups.get_group", return_value=owner_group),
            patch("src.controllers.managed_account_groups.count_accounts_for_owner", return_value=0),
            patch(
                "src.controllers.managed_account_groups.bulk_create_managed_accounts",
                return_value=([(_account(1), "C1"), (_account(2), "C2")], 1),
            ) as mock_bulk,
        ):
            result = bulk_create_accounts(
                session=session,
                user=owner,
                group_id=10,
                body=ManagedAccountBulkCreate(
                    accounts=[
                        ManagedAccountCreate(display_name="Alice"),
                        ManagedAccountCreate(display_name="alice"),
                        ManagedAccountCreate(display_name="Bob"),
                    ]
                ),
            )

        assert mock_bulk.called
        assert len(result.accounts) == 2
        assert result.skipped == 1
        assert result.accounts[0].code == "C1"
