# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Tests for the Stripe webhook event firing in controllers/stripe.py."""

import os

os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")
os.environ.setdefault("TOKEN_HASH_SECRET", "test-secret-not-for-prod")

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from src.controllers.stripe import _apply_subscription_event
from src.helpers.hooks import SubscriptionChanged, _reset_hooks_for_tests, on
from src.models.organization import OrganizationBase
from src.models.user import UserBase


@pytest.fixture(autouse=True)
def reset_hooks():
    _reset_hooks_for_tests()
    yield
    _reset_hooks_for_tests()


def _user_subscription_event(customer_id: str = "cus_USER", unit_amount: int = 1990) -> dict:
    """Build a fake `customer.subscription.created` event payload."""
    return {
        "id": "evt_test_1",
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "customer": customer_id,
                "status": "active",
                "items": {
                    "data": [
                        {
                            "price": {
                                "id": "price_user_tier1",
                                "unit_amount": unit_amount,
                                "metadata": {},
                            }
                        }
                    ]
                },
            }
        },
    }


def _stub_user(user_id: int = 1, customer_id: str = "cus_USER") -> UserBase:
    u = UserBase()
    u.id = user_id
    u.email = "u@example.com"
    u.first_name = "U"
    u.last_name = "E"
    u.display_name = None
    u.is_admin = False
    u.is_premium = False
    u.has_personal_subscription = False
    u.auth_method = "password"
    u.managed_account_group_id = None
    u.deleted_at = None
    u.custom_data = {}
    u.stripe_id = customer_id
    u.created_at = datetime.now(UTC)
    return u


class TestSubscriptionChangedEvent:
    def test_user_subscription_fires_event_with_resolved_user(self):
        """Created/updated paths set `event.user` to the looked-up UserBase."""
        captured: list[SubscriptionChanged] = []

        @on(SubscriptionChanged)
        def _capture(_session, event: SubscriptionChanged):
            captured.append(event)

        session = MagicMock()
        user = _stub_user()
        with (
            patch("src.controllers.stripe.get_user_by_stripe_id", return_value=user),
            patch("src.controllers.stripe.update_user_premium_cache"),
        ):
            _apply_subscription_event(session, _user_subscription_event(), action="created")

        assert len(captured) == 1
        event = captured[0]
        assert event.action == "created"
        assert event.user is user
        assert event.organization is None
        assert event.raw_event["id"] == "evt_test_1"

    def test_org_subscription_fires_event_with_resolved_org(self):
        """Org-priced subs route to the org dispatcher; event carries the org."""
        captured: list[SubscriptionChanged] = []

        @on(SubscriptionChanged)
        def _capture(_session, event: SubscriptionChanged):
            captured.append(event)

        session = MagicMock()
        org = OrganizationBase()
        org.id = 7
        org.stripe_premium = False
        org.stripe_quota = 0

        evt = _user_subscription_event()
        # Override price ID to one that's in ORG_STRIPE_PRICE_IDS
        evt["data"]["object"]["items"]["data"][0]["price"]["id"] = "price_org"

        with (
            patch("src.controllers.stripe.ORG_STRIPE_PRICE_IDS", ["price_org"]),
            patch("src.controllers.stripe.get_organization_by_stripe_id", return_value=org),
            patch("src.controllers.stripe.update_organization"),
            patch("src.controllers.stripe.reset_org_members_premium", return_value=[]),
        ):
            _apply_subscription_event(session, evt, action="updated")

        assert len(captured) == 1
        assert captured[0].organization is org
        assert captured[0].user is None

    def test_handler_runs_in_same_session(self):
        """Handler receives the request-scoped Session passed to fire()."""
        seen_sessions: list = []

        @on(SubscriptionChanged)
        def _capture(session, _event):
            seen_sessions.append(session)

        session = MagicMock()
        with (
            patch("src.controllers.stripe.get_user_by_stripe_id", return_value=_stub_user()),
            patch("src.controllers.stripe.update_user_premium_cache"),
        ):
            _apply_subscription_event(session, _user_subscription_event(), action="created")

        assert seen_sessions == [session]

    def test_zero_amount_subscription_marks_user_not_premium(self):
        """A $0 sub doesn't flip is_premium; event still fires for observers."""
        captured: list[SubscriptionChanged] = []

        @on(SubscriptionChanged)
        def _capture(_session, event):
            captured.append(event)

        session = MagicMock()
        user = _stub_user()
        with (
            patch("src.controllers.stripe.get_user_by_stripe_id", return_value=user),
            patch("src.controllers.stripe.update_user_premium_cache"),
        ):
            _apply_subscription_event(session, _user_subscription_event(unit_amount=0), action="created")

        assert user.has_personal_subscription is False
        assert len(captured) == 1

    def test_deleted_action_passes_is_premium_false(self):
        """Deletion path forces is_premium=False without inspecting the payload."""
        captured: list[SubscriptionChanged] = []

        @on(SubscriptionChanged)
        def _capture(_session, event):
            captured.append(event)

        session = MagicMock()
        user = _stub_user()
        user.has_personal_subscription = True
        with (
            patch("src.controllers.stripe.get_user_by_stripe_id", return_value=user),
            patch("src.controllers.stripe.update_user_premium_cache"),
        ):
            _apply_subscription_event(
                session,
                _user_subscription_event(),
                action="deleted",
                is_premium=False,
            )

        assert user.has_personal_subscription is False
        assert captured[0].action == "deleted"

    def test_unknown_customer_id_skips_starterpack_write_but_still_fires(self):
        """No matching user/org → resolved fields are None; event still fires."""
        captured: list[SubscriptionChanged] = []

        @on(SubscriptionChanged)
        def _capture(_session, event):
            captured.append(event)

        session = MagicMock()
        with patch("src.controllers.stripe.get_user_by_stripe_id", return_value=None):
            _apply_subscription_event(session, _user_subscription_event(customer_id="cus_NOPE"), action="created")

        assert len(captured) == 1
        assert captured[0].user is None
        assert captured[0].organization is None
