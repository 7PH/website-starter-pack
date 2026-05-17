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
    create_account,
    open_as_account,
)
from src.crud import managed_account_groups as crud
from src.helpers import policies
from src.helpers.hooks import ManagedAccountSeatGate, on
from src.models.managed_account_group import ManagedAccountGroupBase
from src.models.user import UserBase
from src.schemas.managed_account import ManagedAccountBulkCreate, ManagedAccountCreate
from src.schemas.user import UserRead


@pytest.fixture
def reset_policy():
    from src.helpers.hooks import _reset_hooks_for_tests

    _reset_hooks_for_tests()
    yield
    _reset_hooks_for_tests()


def _require_premium_to_manage():
    """Register a GroupManagementCheck handler that denies non-premium users."""
    from src.helpers.hooks import GroupManagementCheck, on

    @on(GroupManagementCheck)
    def _handler(_session, event):
        if not event.user.is_premium:
            event.allow = False


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
        result = await policies.get_user_with_manage_groups_perm(_owner(), MagicMock())
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_override_policy_can_block(self, reset_policy):
        _require_premium_to_manage()
        with pytest.raises(HTTPException) as exc:
            await policies.get_user_with_manage_groups_perm(_owner(), MagicMock())
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_override_policy_can_allow_premium(self, reset_policy):
        _require_premium_to_manage()
        u = _owner()
        u.is_premium = True
        result = await policies.get_user_with_manage_groups_perm(u, MagicMock())
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


class TestSeatGate:
    """ManagedAccountSeatGate: per-tier seat-quota hook on the create paths.

    The reset_policy fixture clears every registered hook, so each test
    starts with no handlers (default ``allow=True``).
    """

    def _patches(self, current_count: int = 0):
        """Common patch stack: owned group, count under env cap, CRUD stubbed."""
        owner_group = _group(owner_id=1)
        return (
            patch("src.controllers.managed_account_groups.get_group", return_value=owner_group),
            patch(
                "src.controllers.managed_account_groups.count_accounts_for_owner",
                return_value=current_count,
            ),
            patch(
                "src.controllers.managed_account_groups.create_managed_account",
                return_value=(_account(1), "CODE"),
            ),
            patch(
                "src.controllers.managed_account_groups.bulk_create_managed_accounts",
                return_value=([(_account(1), "C1")], 0),
            ),
        )

    def test_no_handler_allows_create(self, reset_policy):
        """No registered handler → fire returns event.allow=True → controller proceeds."""
        session = MagicMock()
        with self._patches()[0], self._patches()[1], self._patches()[2]:
            result = create_account(
                session=session,
                user=_owner(),
                group_id=10,
                body=ManagedAccountCreate(display_name="Alice"),
            )
        assert result.code == "CODE"

    def test_handler_can_deny_single_create(self, reset_policy):
        @on(ManagedAccountSeatGate)
        def _deny(_session, event):
            event.allow = False

        session = MagicMock()
        with (
            self._patches()[0],
            self._patches()[1],
            self._patches()[2],
            pytest.raises(HTTPException) as exc,
        ):
            create_account(
                session=session,
                user=_owner(),
                group_id=10,
                body=ManagedAccountCreate(display_name="Alice"),
            )

        assert exc.value.status_code == 402

    def test_handler_can_deny_bulk_create(self, reset_policy):
        @on(ManagedAccountSeatGate)
        def _deny(_session, event):
            event.allow = False

        session = MagicMock()
        with (
            self._patches()[0],
            self._patches()[1],
            self._patches()[3],
            pytest.raises(HTTPException) as exc,
        ):
            bulk_create_accounts(
                session=session,
                user=_owner(),
                group_id=10,
                body=ManagedAccountBulkCreate(
                    accounts=[ManagedAccountCreate(display_name="Alice")]
                ),
            )

        assert exc.value.status_code == 402

    def test_reason_propagates_to_response_detail(self, reset_policy):
        @on(ManagedAccountSeatGate)
        def _deny_with_reason(_session, event):
            event.allow = False
            event.reason = "Upgrade to Teacher 50 to add more"

        session = MagicMock()
        with (
            self._patches()[0],
            self._patches()[1],
            self._patches()[2],
            pytest.raises(HTTPException) as exc,
        ):
            create_account(
                session=session,
                user=_owner(),
                group_id=10,
                body=ManagedAccountCreate(display_name="Alice"),
            )

        assert exc.value.status_code == 402
        assert exc.value.detail == "Upgrade to Teacher 50 to add more"

    def test_default_reason_when_handler_omits(self, reset_policy):
        """Handler sets allow=False but leaves reason=None → generic message."""

        @on(ManagedAccountSeatGate)
        def _deny(_session, event):
            event.allow = False  # reason left as None

        session = MagicMock()
        with (
            self._patches()[0],
            self._patches()[1],
            self._patches()[2],
            pytest.raises(HTTPException) as exc,
        ):
            create_account(
                session=session,
                user=_owner(),
                group_id=10,
                body=ManagedAccountCreate(display_name="Alice"),
            )

        assert exc.value.detail == "Seat quota exceeded"

    def test_count_to_create_matches_payload(self, reset_policy):
        captured: list[ManagedAccountSeatGate] = []

        @on(ManagedAccountSeatGate)
        def _capture(_session, event):
            captured.append(event)

        session = MagicMock()

        # Single create → count_to_create = 1.
        with self._patches()[0], self._patches()[1], self._patches()[2]:
            create_account(
                session=session,
                user=_owner(),
                group_id=10,
                body=ManagedAccountCreate(display_name="Alice"),
            )

        # Bulk of 25 → count_to_create = 25 (worst case, pre-dedup).
        with self._patches()[0], self._patches()[1], self._patches()[3]:
            bulk_create_accounts(
                session=session,
                user=_owner(),
                group_id=10,
                body=ManagedAccountBulkCreate(
                    accounts=[ManagedAccountCreate(display_name=f"S{i}") for i in range(25)]
                ),
            )

        assert [e.count_to_create for e in captured] == [1, 25]
        assert all(e.group_id == 10 and e.user.id == 1 for e in captured)

    def test_handler_runs_in_same_session(self, reset_policy):
        """Handler receives the request-scoped Session passed in by the controller."""
        seen_sessions: list = []

        @on(ManagedAccountSeatGate)
        def _capture(session, _event):
            seen_sessions.append(session)

        session = MagicMock()
        with self._patches()[0], self._patches()[1], self._patches()[2]:
            create_account(
                session=session,
                user=_owner(),
                group_id=10,
                body=ManagedAccountCreate(display_name="Alice"),
            )

        assert seen_sessions == [session]

    def test_env_cap_still_runs_first(self, reset_policy):
        """Env cap exceeded → 400 with env-cap detail; the new hook never fires."""
        fired: list = []

        @on(ManagedAccountSeatGate)
        def _record(_session, event):
            fired.append(event)

        session = MagicMock()
        with (
            patch(
                "src.controllers.managed_account_groups.get_group",
                return_value=_group(owner_id=1),
            ),
            patch(
                "src.controllers.managed_account_groups.count_accounts_for_owner",
                return_value=999,
            ),
            patch("src.controllers.managed_account_groups.MANAGED_ACCOUNTS_MAX_PER_USER", 1000),
            pytest.raises(HTTPException) as exc,
        ):
            bulk_create_accounts(
                session=session,
                user=_owner(),
                group_id=10,
                body=ManagedAccountBulkCreate(
                    accounts=[
                        ManagedAccountCreate(display_name="A"),
                        ManagedAccountCreate(display_name="B"),
                    ]
                ),
            )

        assert exc.value.status_code == 400
        assert "1000 managed-account quota" in exc.value.detail
        assert fired == []  # hook never fired
