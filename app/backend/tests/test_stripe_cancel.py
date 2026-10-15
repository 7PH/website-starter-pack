# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""A subscription scheduled to end shows as canceling, whichever field Stripe used."""

import os

os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")
os.environ.setdefault("TOKEN_HASH_SECRET", "test-secret-not-for-prod")

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.helpers.stripe import _parse_subscription

END = 1794705184


@pytest.mark.parametrize(
    ("cancel_at_period_end", "cancel_at", "canceling"),
    [
        (False, None, False),
        (True, END, True),  # older API versions and the API's own cancel_at_period_end
        (False, END, True),  # customer portal on recent API versions
    ],
)
def test_parse_subscription_cancel(cancel_at_period_end, cancel_at, canceling):
    sub = SimpleNamespace(id="sub_1", cancel_at_period_end=cancel_at_period_end, cancel_at=cancel_at)
    with patch("src.helpers.stripe.stripe.SubscriptionItem.list") as items:
        items.return_value.auto_paging_iter.return_value = []
        parsed = _parse_subscription(sub)
    assert parsed["cancel_at_period_end"] is canceling
    assert (parsed["expires_at"] is not None) is canceling
