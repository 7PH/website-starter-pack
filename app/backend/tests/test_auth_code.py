# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Tests for the POST /auth/code sign-in-by-code endpoint."""

import os

# helpers.db reads APP_DB_* at module load; auth.py reads TOKEN_HASH_SECRET.
os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")
os.environ.setdefault("TOKEN_HASH_SECRET", "test-secret-not-for-prod")

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from src.controllers.auth import sign_in_with_code
from src.helpers.hooks import AccessCodeResolution, _reset_hooks_for_tests, on
from src.models.user import UserBase
from src.schemas.user import SignInWithCodeRequest


@pytest.fixture
def reset_hooks():
    """Clear all hook handlers before and after each test."""
    _reset_hooks_for_tests()
    yield
    _reset_hooks_for_tests()


def _resolve_with(fn):
    """Register an AccessCodeResolution handler that delegates to ``fn``.

    ``fn`` matches the legacy ``(account_id, code, request) -> UserBase | None``
    shape so the per-test bodies stay short.
    """

    @on(AccessCodeResolution)
    def _handler(_session, event):
        if event.user is None:
            event.user = fn(event.managed_account_id, event.code, event.request)


def _stub_user(user_id: int = 42) -> UserBase:
    """Build a UserBase that looks like a managed account user."""
    user = UserBase()
    user.id = user_id
    user.email = None
    user.first_name = None
    user.last_name = None
    user.display_name = "Étoile"
    user.is_admin = False
    user.is_premium = False
    user.has_personal_subscription = False
    user.auth_method = "access_code"
    user.managed_account_group_id = 7
    user.custom_data = {}
    return user


def _stub_request() -> MagicMock:
    request = MagicMock()
    request.client = SimpleNamespace(host="127.0.0.1")
    request.headers = {}
    return request


def _body(account_id: int = 42, code: str = "OK") -> SignInWithCodeRequest:
    return SignInWithCodeRequest(managed_account_id=account_id, code=code)


class TestSignInWithCode:
    def test_unconfigured_endpoint_returns_404(self, reset_hooks):
        """No validator registered → endpoint behaves as if it doesn't exist."""
        with patch("src.controllers.auth.ensure_rate_limit"), pytest.raises(HTTPException) as exc:
            sign_in_with_code(
                request=_stub_request(),
                session=MagicMock(),
                body=_body(),
            )
        assert exc.value.status_code == 404

    def test_valid_id_and_code_issues_jwt(self, reset_hooks):
        """Validator accepts (account_id, code); we get a Bearer token back."""
        _resolve_with(
            lambda account_id, code, _req: _stub_user(account_id) if code == "OK" else None
        )

        with (
            patch("src.controllers.auth.log_event"),
            patch("src.controllers.auth.ensure_rate_limit"),
            # Stub the manager-lookup so the test doesn't depend on a real DB.
            patch("src.helpers.auth.is_premium_effective", return_value=False),
        ):
            result = sign_in_with_code(
                request=_stub_request(),
                session=MagicMock(),
                body=_body(account_id=42, code="OK"),
            )

        assert result.access_token
        assert result.token_type == "bearer"
        assert result.user.id == 42
        assert result.user.auth_method == "access_code"
        assert result.user.email is None
        assert result.user.managed_account_group_id == 7

    def test_invalid_code_returns_401(self, reset_hooks):
        """Validator returning None surfaces as 401."""
        _resolve_with(lambda _id, _code, _req: None)

        with (
            patch("src.controllers.auth.log_event") as mock_log,
            patch("src.controllers.auth.ensure_rate_limit"),
            pytest.raises(HTTPException) as exc,
        ):
            sign_in_with_code(
                request=_stub_request(),
                session=MagicMock(),
                body=_body(account_id=42, code="NOPE"),
            )

        assert exc.value.status_code == 401
        # Failure log includes the account_id and a hashed-prefix of the code.
        mock_log.assert_called_once()
        details = mock_log.call_args.kwargs.get("details", {})
        assert details.get("managed_account_id") == 42
        assert "code_hash" in details
        assert "NOPE" not in str(details)

    def test_id_mismatch_returns_401(self, reset_hooks):
        """A correct code paired with the wrong account_id is still rejected."""
        _resolve_with(
            lambda account_id, code, _req: _stub_user(account_id) if (account_id == 42 and code == "OK") else None
        )

        with (
            patch("src.controllers.auth.log_event"),
            patch("src.controllers.auth.ensure_rate_limit"),
            pytest.raises(HTTPException) as exc,
        ):
            sign_in_with_code(
                request=_stub_request(),
                session=MagicMock(),
                body=_body(account_id=99, code="OK"),
            )
        assert exc.value.status_code == 401
