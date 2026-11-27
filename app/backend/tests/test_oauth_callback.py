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

from src.controllers import oauth
from src.schemas.oauth import OAuthCallbackRequest


def test_new_google_user_is_created_as_oauth():
    """The users_auth_integrity CHECK rejects a 'password' user with an oauth_provider."""
    google_user = SimpleNamespace(id="g-123", email="New@Example.com", first_name="Ada", last_name="Lovelace")
    with (
        patch.object(oauth, "is_oauth_enabled", return_value=True),
        patch.object(oauth, "ensure_rate_limit"),
        patch.object(oauth, "get_client_ip", return_value="127.0.0.1"),
        patch.object(oauth, "get_user_from_code", AsyncMock(return_value=google_user)),
        patch.object(oauth, "get_user_by_email", return_value=None),
        patch.object(oauth, "create_user") as create_user,
        patch.object(oauth, "setup_new_user_stripe"),
        patch.object(oauth, "log_event"),
        patch.object(oauth, "issue_jwt_with_orgs"),
    ):
        asyncio.run(
            oauth.handle_google_callback(
                request=MagicMock(),
                session=MagicMock(),
                body=OAuthCallbackRequest(code="code", state="state"),
            )
        )

    user = create_user.call_args.args[1]
    assert user.auth_method == "oauth"
    assert user.oauth_provider == "google"
    assert user.email == "new@example.com"
