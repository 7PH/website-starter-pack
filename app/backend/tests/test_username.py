# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Tests for username validation and the privacy of the public user schema."""

import os

# Importing src pulls in helpers.db which reads APP_DB_* at module load.
os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.crud.users import is_username_taken
from src.helpers import user_display
from src.helpers.username import UsernameError, validate_username
from src.schemas import user as user_schemas
from src.schemas.user import UserCreate, UserPreviewRead, require_email_shape


@pytest.fixture
def usernames_on(monkeypatch):
    """Both modules bind USERNAMES_ENABLED at import, so both need patching."""
    monkeypatch.setattr(user_display, "USERNAMES_ENABLED", True)
    monkeypatch.setattr(user_schemas, "USERNAMES_ENABLED", True)


@pytest.fixture
def usernames_off(monkeypatch):
    monkeypatch.setattr(user_display, "USERNAMES_ENABLED", False)
    monkeypatch.setattr(user_schemas, "USERNAMES_ENABLED", False)


class TestValidateUsername:
    def test_accepts_the_allowed_charset(self):
        assert validate_username("risi_bank-42") == "risi_bank-42"

    def test_preserves_case(self):
        assert validate_username("RisiBank") == "RisiBank"

    def test_trims_surrounding_whitespace(self):
        assert validate_username("  risibank  ") == "risibank"

    @pytest.mark.parametrize("value", ["a", "x" * 33, "has space", "accént", "dot.dot", "sla/sh"])
    def test_rejects_bad_shapes(self, value):
        with pytest.raises(UsernameError):
            validate_username(value)

    def test_rejects_at_sign_so_it_cannot_shadow_an_email(self):
        with pytest.raises(UsernameError):
            validate_username("bob@gmail.com")




class TestCharset:
    def test_allows_forum_style_brackets(self):
        assert validate_username("Kim[2]") == "Kim[2]"
        assert validate_username("[Pseudo]") == "[Pseudo]"

    def test_allows_two_character_handles(self):
        assert validate_username("ab") == "ab"


class TestEmailShape:
    """Usernames forbid '@'; requiring it on the email side is what makes that
    a real separation rather than a convention."""

    @pytest.mark.parametrize("value", ["collide", "risibank", "@nolocal.com", "nodomain@", "  ", ""])
    def test_rejects_addresses_that_could_collide_with_a_handle(self, value):
        with pytest.raises(ValueError):
            require_email_shape(value)

    @pytest.mark.parametrize(
        "value", ["a@b.com", "admin@localhost", "tester+tag@example.co.uk", "user@preview.app"]
    )
    def test_accepts_real_addresses_including_ones_EmailStr_rejects(self, value):
        assert require_email_shape(value) == value

    def test_signup_rejects_an_email_with_no_at_sign(self):
        with pytest.raises(ValueError):
            UserCreate(email="collide", password="testpass123", first_name="A", last_name="B")


class TestIsUsernameTaken:
    def test_free_when_nobody_holds_it(self):
        with patch("src.crud.users.get_user_by_username", return_value=None):
            assert is_username_taken(MagicMock(), "risibank") is False

    def test_taken_when_another_user_holds_it(self):
        with patch("src.crud.users.get_user_by_username", return_value=SimpleNamespace(id=2)):
            assert is_username_taken(MagicMock(), "risibank", exclude_user_id=1) is True

    def test_own_handle_is_not_taken_against_itself(self):
        """A capitalization-only rename must not 409 on the user's own row."""
        with patch("src.crud.users.get_user_by_username", return_value=SimpleNamespace(id=1)):
            assert is_username_taken(MagicMock(), "RisiBank", exclude_user_id=1) is False


class TestPublicSchemaPrivacy:
    def test_username_is_exposed_as_the_public_label(self, usernames_on):
        preview = UserPreviewRead.model_validate(
            SimpleNamespace(
                id=1,
                username="risibank",
                first_name="Alice",
                last_name="Doe",
                display_name=None,
                auth_method="password",
                custom_data={},
            )
        )
        assert preview.username == "risibank"
        assert preview.display_label == "risibank"

    def test_username_hidden_from_the_api_when_the_feature_is_off(self, usernames_off):
        """Matches display_for's gating: a pre-existing column stays invisible."""
        preview = UserPreviewRead.model_validate(
            SimpleNamespace(
                id=1,
                username="risibank",
                first_name="Alice",
                last_name="Doe",
                display_name=None,
                auth_method="password",
                custom_data={},
            )
        )
        assert preview.username is None
        assert preview.display_label == "Alice D."

    def test_never_leaks_an_email_as_the_public_label(self):
        """The label renders next to public content, so it must never fall to the email."""
        preview = UserPreviewRead.model_validate(
            SimpleNamespace(
                id=1,
                username=None,
                first_name=None,
                last_name=None,
                display_name=None,
                email="alice@example.com",
                auth_method="password",
                custom_data={},
            )
        )
        assert "email" not in preview.model_dump()
        assert preview.display_label is None
