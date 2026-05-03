# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Tests for the public /config endpoint."""

import os

# Importing src.controllers.config pulls in helpers.db transitively, which
# reads APP_DB_* at module load. Seed dummies before any import.
os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")

from src import constants
from src.controllers.config import get_config
from src.schemas.config_ext import BackendConfig


class TestGetConfig:
    """get_config returns a BackendConfig populated from constants."""

    def test_returns_backend_config(self):
        result = get_config()
        assert isinstance(result, BackendConfig)

    def test_core_fields_present_with_correct_types(self):
        result = get_config()
        # Limits & validation
        assert isinstance(result.password_min_length, int)
        assert isinstance(result.org_max_per_user, int)
        assert isinstance(result.org_max_members, int)
        assert isinstance(result.org_invitation_expiry_days, int)
        assert isinstance(result.managed_account_group_max_per_user, int)
        assert isinstance(result.managed_accounts_max_per_user, int)
        # Feature flags
        assert isinstance(result.stripe_enabled, bool)
        assert isinstance(result.organizations_enabled, bool)
        assert isinstance(result.org_invitations_enabled, bool)
        assert isinstance(result.managed_accounts_enabled, bool)
        assert isinstance(result.llm_enabled, bool)
        assert isinstance(result.org_self_service_subscriptions, bool)
        assert isinstance(result.org_self_service_creation, bool)
        # LLM info
        assert isinstance(result.llm_provider, str)
        assert isinstance(result.llm_model, str)

    def test_password_min_length_matches_constant(self):
        assert get_config().password_min_length == constants.PASSWORD_MIN_LENGTH

    def test_stripe_flag_reflects_constant(self, monkeypatch):
        monkeypatch.setattr(constants, "STRIPE_ENABLED", True)
        assert get_config().stripe_enabled is True

        monkeypatch.setattr(constants, "STRIPE_ENABLED", False)
        assert get_config().stripe_enabled is False

    def test_organizations_flag_reflects_constant(self, monkeypatch):
        monkeypatch.setattr(constants, "ORGANIZATIONS_ENABLED", True)
        assert get_config().organizations_enabled is True

        monkeypatch.setattr(constants, "ORGANIZATIONS_ENABLED", False)
        assert get_config().organizations_enabled is False

    def test_llm_provider_and_model_blank_when_disabled(self, monkeypatch):
        monkeypatch.setattr(constants, "LLM_ENABLED", False)
        monkeypatch.setattr(constants, "LLM_PROVIDER", "anthropic")
        monkeypatch.setattr(constants, "LLM_MODEL", "claude-sonnet-4")

        result = get_config()
        assert result.llm_enabled is False
        assert result.llm_provider == ""
        assert result.llm_model == ""

    def test_llm_provider_and_model_populated_when_enabled(self, monkeypatch):
        monkeypatch.setattr(constants, "LLM_ENABLED", True)
        monkeypatch.setattr(constants, "LLM_PROVIDER", "anthropic")
        monkeypatch.setattr(constants, "LLM_MODEL", "claude-sonnet-4")

        result = get_config()
        assert result.llm_enabled is True
        assert result.llm_provider == "anthropic"
        assert result.llm_model == "claude-sonnet-4"
