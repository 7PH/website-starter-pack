# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""An admin-assigned org plan has no Stripe subscription, and Stripe must not cancel it."""

import os

os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")
os.environ.setdefault("TOKEN_HASH_SECRET", "test-secret-not-for-prod")

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.controllers import organizations
from src.controllers import stripe as stripe_controller


def _assigned_org():
    return SimpleNamespace(
        id=7, stripe_id="cus_ORG", billing_price_id="price_org", stripe_premium=True, stripe_quota=50
    )


def test_billing_tab_keeps_admin_assigned_plan():
    org = _assigned_org()
    with (
        patch.object(organizations, "_ensure_billing_enabled"),
        patch.object(organizations, "_check_org_access", return_value=org),
        patch.object(organizations, "stripe_helper") as stripe_helper,
        patch.object(organizations, "reset_org_members_premium") as reset,
    ):
        status = organizations.get_org_subscription(session=MagicMock(), user=MagicMock(), org_id=org.id)

    assert status.stripe_premium is True
    assert status.stripe_quota == 50
    assert (org.stripe_premium, org.stripe_quota) == (True, 50)
    stripe_helper.get_org_subscription_status.assert_not_called()
    reset.assert_not_called()


def test_webhook_keeps_admin_assigned_plan():
    org = _assigned_org()
    with (
        patch.object(stripe_controller, "get_organization_by_stripe_id", return_value=org),
        patch.object(stripe_controller, "update_organization") as update,
        patch.object(stripe_controller, "reset_org_members_premium") as reset,
    ):
        result = stripe_controller._apply_org_subscription(MagicMock(), "cus_ORG", is_premium=False, seats=0)

    assert result is org
    assert (org.stripe_premium, org.stripe_quota) == (True, 50)
    update.assert_not_called()
    reset.assert_not_called()
