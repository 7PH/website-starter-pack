# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
"""App Stripe params (helpers/stripe_ext.py) reach the Stripe calls, and win over core's."""

from unittest.mock import patch

from src.helpers import stripe as stripe_helper


def _checkout_kwargs(params: dict) -> dict:
    with (
        patch.object(stripe_helper, "STRIPE_ENABLED", True),
        patch.object(stripe_helper, "CHECKOUT_SESSION_PARAMS", params),
        patch.object(stripe_helper, "invalidate_subscription_cache"),
        patch("src.helpers.stripe.stripe.checkout.Session.create") as create,
    ):
        stripe_helper.create_checkout_session("cus_1", "price_1", "https://ok", "https://ko")
    return create.call_args.kwargs


def test_checkout_unchanged_without_app_params():
    assert _checkout_kwargs({}) == {
        "customer": "cus_1",
        "payment_method_types": ["card"],
        "line_items": [{"price": "price_1", "quantity": 1}],
        "mode": "subscription",
        "success_url": "https://ok",
        "cancel_url": "https://ko",
    }


def test_checkout_gets_app_params_which_win_over_core():
    kwargs = _checkout_kwargs({"locale": "fr", "payment_method_types": ["card", "sepa_debit"]})
    assert kwargs["locale"] == "fr"
    assert kwargs["payment_method_types"] == ["card", "sepa_debit"]
    assert kwargs["customer"] == "cus_1"


def test_billing_portal_and_new_customers_get_app_params():
    with (
        patch.object(stripe_helper, "STRIPE_ENABLED", True),
        patch.object(stripe_helper, "BILLING_PORTAL_PARAMS", {"locale": "fr"}),
        patch.object(stripe_helper, "CUSTOMER_PARAMS", {"preferred_locales": ["fr"]}),
        patch("src.helpers.stripe.stripe.billing_portal.Session.create") as portal,
        patch("src.helpers.stripe.stripe.Customer.create") as create_customer,
    ):
        stripe_helper.create_billing_portal_session("cus_1", "https://back")
        stripe_helper.sync_org_customer(org_id=7, email="org@example.com", name="Org", existing_stripe_id=None)
    assert portal.call_args.kwargs == {"customer": "cus_1", "return_url": "https://back", "locale": "fr"}
    assert create_customer.call_args.kwargs["preferred_locales"] == ["fr"]
