# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Tests for the internal controller (mint-token + seed-users).

Both routes share gating via `_require_internal_key`. The seed-users endpoint
is the new addition: it upserts a roster of password-auth users so preview
stacks (and local dev) come up with known logins.
"""

import os
from unittest.mock import MagicMock, patch

os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")
os.environ.setdefault("TOKEN_HASH_SECRET", "test-secret-not-for-prod")

import pytest
from fastapi import HTTPException

from src.controllers import internal
from src.controllers.internal import (
    SeedUserSpec,
    SeedUsersRequest,
    _require_internal_key,
    seed_users,
)
from src.models.user import UserBase


def _spec(email: str, **overrides) -> SeedUserSpec:
    return SeedUserSpec(email=email, password="pw", **overrides)


class TestRequireInternalKey:
    def test_rejects_when_key_unset(self, monkeypatch):
        """Empty server-side key → 401 even if the caller sends nothing."""
        monkeypatch.setattr(internal, "INTERNAL_API_KEY", "")
        with pytest.raises(HTTPException) as exc:
            _require_internal_key(x_internal_api_key="")
        assert exc.value.status_code == 401

    def test_rejects_when_caller_wrong(self, monkeypatch):
        monkeypatch.setattr(internal, "INTERNAL_API_KEY", "real-key")
        with pytest.raises(HTTPException) as exc:
            _require_internal_key(x_internal_api_key="wrong")
        assert exc.value.status_code == 401

    def test_rejects_non_ascii_header(self, monkeypatch):
        """Non-ASCII caller key → 401, not a TypeError bubbling up as a 500."""
        monkeypatch.setattr(internal, "INTERNAL_API_KEY", "real-key")
        with pytest.raises(HTTPException) as exc:
            _require_internal_key(x_internal_api_key="clé")
        assert exc.value.status_code == 401

    def test_accepts_when_match(self, monkeypatch):
        monkeypatch.setattr(internal, "INTERNAL_API_KEY", "real-key")
        # No exception = pass.
        _require_internal_key(x_internal_api_key="real-key")


class TestSeedUsers:
    def test_creates_new_users(self):
        """Unknown emails → create_user is called once per spec, status='created'."""
        session = MagicMock()
        with (
            patch("src.controllers.internal.get_user_by_email", return_value=None),
            patch("src.controllers.internal.create_user") as mock_create,
            patch("src.controllers.internal.hash_password", return_value="hashed"),
        ):
            result = seed_users(
                payload=SeedUsersRequest(
                    users=[_spec("admin@preview.app", is_admin=True), _spec("u@preview.app")]
                ),
                session=session,
            )
        assert mock_create.call_count == 2
        assert [r.status for r in result.results] == ["created", "created"]
        # Both users should be UserBase rows with email_confirmed=True and auth_method='password'.
        created_users = [call.args[1] for call in mock_create.call_args_list]
        assert all(isinstance(u, UserBase) for u in created_users)
        assert all(u.email_confirmed is True for u in created_users)
        assert all(u.auth_method == "password" for u in created_users)
        assert created_users[0].is_admin is True
        assert created_users[1].is_admin is False

    def test_updates_existing_users(self):
        """Known emails → update flags in place, status='updated'. No create_user call."""
        session = MagicMock()
        existing = UserBase()
        existing.email = "admin@preview.app"
        existing.is_admin = False
        existing.is_premium = False
        with (
            patch("src.controllers.internal.get_user_by_email", return_value=existing),
            patch("src.controllers.internal.create_user") as mock_create,
            patch("src.controllers.internal.hash_password", return_value="new-hash"),
        ):
            result = seed_users(
                payload=SeedUsersRequest(
                    users=[_spec("admin@preview.app", is_admin=True, is_premium=True)]
                ),
                session=session,
            )
        assert mock_create.call_count == 0
        assert result.results[0].status == "updated"
        assert existing.is_admin is True
        assert existing.is_premium is True
        assert existing.hashed_password == "new-hash"
        assert existing.email_confirmed is True
        session.commit.assert_called()

    def test_idempotent_second_run(self):
        """Running the same payload twice → second run sees every user as existing."""
        session = MagicMock()
        # First run: no users exist. Second run: same emails come back.
        store: dict[str, UserBase] = {}

        def fake_get(_session, email):
            return store.get(email)

        def fake_create(_session, user):
            store[user.email] = user

        with (
            patch("src.controllers.internal.get_user_by_email", side_effect=fake_get),
            patch("src.controllers.internal.create_user", side_effect=fake_create),
            patch("src.controllers.internal.hash_password", return_value="h"),
        ):
            payload = SeedUsersRequest(users=[_spec("a@preview.app"), _spec("b@preview.app")])
            first = seed_users(payload=payload, session=session)
            second = seed_users(payload=payload, session=session)

        assert [r.status for r in first.results] == ["created", "created"]
        assert [r.status for r in second.results] == ["updated", "updated"]
        assert set(store.keys()) == {"a@preview.app", "b@preview.app"}

    def test_lowercases_email(self):
        """Spec emails with mixed case → stored lowercased, looked up lowercased."""
        session = MagicMock()
        seen_emails: list[str] = []

        def fake_get(_session, email):
            seen_emails.append(email)
            return None

        with (
            patch("src.controllers.internal.get_user_by_email", side_effect=fake_get),
            patch("src.controllers.internal.create_user") as mock_create,
            patch("src.controllers.internal.hash_password", return_value="h"),
        ):
            seed_users(
                payload=SeedUsersRequest(users=[_spec("MixedCase@Preview.App")]),
                session=session,
            )
        assert seen_emails == ["mixedcase@preview.app"]
        assert mock_create.call_args.args[1].email == "mixedcase@preview.app"
