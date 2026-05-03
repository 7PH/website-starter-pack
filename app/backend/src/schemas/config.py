# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Pydantic schema for the public /config endpoint."""

from pydantic import BaseModel


class CoreBackendConfig(BaseModel):
    """Core backend constants exposed to the frontend.

    Sub-apps extend this by subclassing in ``schemas/config_ext.py``.

    Fields are kept required (no defaults) so the generated TypeScript types
    treat them as always-present. Values are filled by the controller, which
    reads from ``constants`` and from ``build_extra()`` for sub-app fields.
    """

    # Limits & validation
    password_min_length: int
    org_max_per_user: int
    org_max_members: int
    org_invitation_expiry_days: int
    managed_account_group_max_per_user: int
    managed_accounts_max_per_user: int

    # Feature flags
    stripe_enabled: bool
    organizations_enabled: bool
    org_invitations_enabled: bool
    managed_accounts_enabled: bool
    llm_enabled: bool
    org_self_service_subscriptions: bool
    org_self_service_creation: bool

    # LLM info (empty strings when LLM disabled)
    llm_provider: str
    llm_model: str
