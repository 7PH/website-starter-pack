# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Tests for the display-name fallback ladder."""

import os

# Importing src pulls in helpers.db which reads APP_DB_* at module load.
os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")

from types import SimpleNamespace

from src.helpers.user_display import display_for


def _user(**kwargs):
    """Build a duck-typed user with sensible defaults."""
    base = {
        "auth_method": "password",
        "display_name": None,
        "first_name": None,
        "last_name": None,
        "email": None,
    }
    base.update(kwargs)
    return SimpleNamespace(**base)


class TestDisplayFor:
    def test_display_name_wins(self):
        user = _user(display_name="Étoile", first_name="Alice", last_name="Doe", email="a@b.c")
        assert display_for(user) == "Étoile"

    def test_full_name_when_no_display_name(self):
        assert display_for(_user(first_name="Alice", last_name="Doe")) == "Alice Doe"

    def test_falls_back_to_email_when_no_name(self):
        assert display_for(_user(email="alice@example.com")) == "alice@example.com"

    def test_returns_none_when_nothing_set(self):
        assert display_for(_user()) is None

    def test_deleted_user_returns_none_even_with_display_name(self):
        user = _user(auth_method="deleted", display_name="Ignored", email="x@y.z")
        assert display_for(user) is None

    def test_first_name_only_falls_through_to_email(self):
        user = _user(first_name="Alice", email="a@b.c")
        assert display_for(user) == "a@b.c"
