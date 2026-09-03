# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Public /config endpoint exposing backend constants to the frontend."""

from fastapi import APIRouter, status

from .. import constants
from ..helpers.username import USERNAME_PATTERN
from ..schemas.config_ext import BackendConfig, build_extra

router = APIRouter()


@router.get("/config", response_model=BackendConfig, status_code=status.HTTP_200_OK)
def get_config() -> BackendConfig:
    """Public, unauthenticated snapshot of backend constants for the frontend."""
    return BackendConfig(
        password_min_length=constants.PASSWORD_MIN_LENGTH,
        org_max_per_user=constants.ORG_MAX_PER_USER,
        org_max_members=constants.ORG_MAX_MEMBERS,
        org_invitation_expiry_days=constants.ORG_INVITATION_EXPIRY_DAYS,
        managed_account_group_max_per_user=constants.MANAGED_ACCOUNT_GROUP_MAX_PER_USER,
        managed_accounts_max_per_user=constants.MANAGED_ACCOUNTS_MAX_PER_USER,
        stripe_enabled=constants.STRIPE_ENABLED,
        organizations_enabled=constants.ORGANIZATIONS_ENABLED,
        org_invitations_enabled=constants.ORG_INVITATIONS_ENABLED,
        managed_accounts_enabled=constants.MANAGED_ACCOUNTS_ENABLED,
        usernames_enabled=constants.USERNAMES_ENABLED,
        username_pattern=USERNAME_PATTERN.pattern,
        llm_enabled=constants.LLM_ENABLED,
        org_self_service_subscriptions=constants.ORG_SELF_SERVICE_SUBSCRIPTIONS,
        org_self_service_creation=constants.ORG_SELF_SERVICE_CREATION,
        llm_provider=constants.LLM_PROVIDER if constants.LLM_ENABLED else "",
        llm_model=constants.LLM_MODEL if constants.LLM_ENABLED else "",
        **build_extra(),
    )
