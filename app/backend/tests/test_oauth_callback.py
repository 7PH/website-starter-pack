# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Tests for the Google OAuth callback."""

import os

# helpers.db reads APP_DB_* at module load; auth.py reads TOKEN_HASH_SECRET.
os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")
os.environ.setdefault("TOKEN_HASH_SECRET", "test-secret-not-for-prod")

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.controllers import oauth
from src.helpers import oauth as oauth_helper
from src.helpers.auth import create_access_token
from src.schemas.oauth import OAuthCallbackRequest
from src.schemas.user import UserRead


def _token():
    return create_access_token(UserRead(id=1, email="a@example.com", is_admin=False, is_premium=False), token_version=0)


def test_existing_google_user_is_not_a_new_user():
    google_user = SimpleNamespace(id="g-1", email="a@example.com", first_name="", last_name="", verified_email=True)
    with (
        patch.object(oauth, "is_oauth_enabled", return_value=True),
        patch.object(oauth, "ensure_rate_limit"),
        patch.object(oauth, "get_client_ip", return_value="127.0.0.1"),
        patch.object(oauth, "get_user_from_code", AsyncMock(return_value=google_user)),
        patch.object(oauth, "get_user_by_email", return_value=SimpleNamespace(id=1, email_confirmed=True)),
        patch.object(oauth, "log_event"),
        patch.object(oauth, "issue_jwt_with_orgs", return_value=_token()),
    ):
        response = asyncio.run(
            oauth.handle_google_callback(
                request=MagicMock(), session=MagicMock(), body=OAuthCallbackRequest(code="code", state="state")
            )
        )
    assert response.is_new_user is False


def test_new_google_user_is_created_as_oauth():
    """The users_auth_integrity CHECK rejects a 'password' user with an oauth_provider."""
    google_user = SimpleNamespace(
        id="g-123", email="New@Example.com", first_name="Ada", last_name="Lovelace", verified_email=True
    )
    with (
        patch.object(oauth, "is_oauth_enabled", return_value=True),
        patch.object(oauth, "ensure_rate_limit"),
        patch.object(oauth, "get_client_ip", return_value="127.0.0.1"),
        patch.object(oauth, "get_user_from_code", AsyncMock(return_value=google_user)),
        patch.object(oauth, "get_user_by_email", return_value=None),
        patch.object(oauth, "create_user") as create_user,
        patch.object(oauth, "setup_new_user_stripe"),
        patch.object(oauth, "log_event"),
        patch.object(oauth, "issue_jwt_with_orgs", return_value=_token()),
    ):
        response = asyncio.run(
            oauth.handle_google_callback(
                request=MagicMock(),
                session=MagicMock(),
                body=OAuthCallbackRequest(code="code", state="state"),
            )
        )

    assert response.is_new_user is True
    user = create_user.call_args.args[1]
    assert user.auth_method == "oauth"
    assert user.oauth_provider == "google"
    assert user.email == "new@example.com"


def test_unverified_google_email_can_neither_sign_up_nor_link():
    google_user = SimpleNamespace(
        id="g-1", email="taken@example.com", first_name="", last_name="", verified_email=False
    )
    with (
        patch.object(oauth, "is_oauth_enabled", return_value=True),
        patch.object(oauth, "ensure_rate_limit"),
        patch.object(oauth, "get_client_ip", return_value="127.0.0.1"),
        patch.object(oauth, "get_user_from_code", AsyncMock(return_value=google_user)),
        patch.object(oauth, "get_user_by_email") as get_user_by_email,
        patch.object(oauth, "create_user") as create_user,
        pytest.raises(HTTPException) as exc,
    ):
        asyncio.run(
            oauth.handle_google_callback(
                request=MagicMock(), session=MagicMock(), body=OAuthCallbackRequest(code="code", state="state")
            )
        )
    assert exc.value.status_code == 400
    get_user_by_email.assert_not_called()
    create_user.assert_not_called()


@pytest.mark.parametrize(("payload", "verified"), [({"verified_email": True}, True), ({}, False)])
def test_userinfo_reads_verified_email(payload, verified):
    response = MagicMock()
    response.json.return_value = {"id": "g-1", "email": "a@example.com", **payload}
    client = MagicMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    client.get = AsyncMock(return_value=response)
    with patch.object(oauth_helper.httpx, "AsyncClient", return_value=client):
        info = asyncio.run(oauth_helper.get_google_user_info("token"))
    assert info.verified_email is verified
