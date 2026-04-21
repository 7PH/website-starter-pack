# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Tests for admin-managed organization billing: sign flipping and cycle math."""

import os

# Importing src.tasks.billing pulls in helpers.db, which reads APP_DB_* at module
# load. CI runs pytest without those env vars, so seed dummies before any import.
os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.helpers import stripe as stripe_helper


class TestComputeNextCycleEnd:
    """compute_next_cycle_end advances a boundary by one billing interval."""

    def test_month_default(self):
        start = datetime(2026, 1, 15, 12, 0, 0)
        end = stripe_helper.compute_next_cycle_end("month", start)
        assert end == start + timedelta(days=30)

    def test_year(self):
        start = datetime(2026, 3, 1, 0, 0, 0)
        end = stripe_helper.compute_next_cycle_end("year", start)
        assert end.year == 2027
        assert end.month == 3
        assert end.day == 1

    def test_week(self):
        start = datetime(2026, 4, 1)
        end = stripe_helper.compute_next_cycle_end("week", start)
        assert end == start + timedelta(weeks=1)

    def test_day(self):
        start = datetime(2026, 4, 1, 8, 0, 0)
        end = stripe_helper.compute_next_cycle_end("day", start)
        assert end == start + timedelta(days=1)

    def test_interval_count(self):
        start = datetime(2026, 1, 1)
        end = stripe_helper.compute_next_cycle_end("day", start, interval_count=3)
        assert end == start + timedelta(days=3)

    def test_unknown_interval_falls_back_to_month(self):
        start = datetime(2026, 1, 1)
        end = stripe_helper.compute_next_cycle_end("bogus", start)
        assert end == start + timedelta(days=30)


class TestAdjustOrgBalance:
    """adjust_org_balance flips sign at the Stripe boundary."""

    def test_positive_amount_sends_negative_to_stripe(self):
        """Admin credits org +1000 → Stripe gets -1000 (their credit convention)."""
        fake_tx = SimpleNamespace(
            id="txn_1",
            amount=-1000,
            currency="eur",
            description="payment received",
            created=1_700_000_000,
            type="adjustment",
        )
        with patch.object(stripe_helper, "STRIPE_ENABLED", True), \
             patch.object(stripe_helper.stripe.Customer, "create_balance_transaction",
                          return_value=fake_tx) as mock_create:
            result = stripe_helper.adjust_org_balance(
                stripe_customer_id="cus_abc",
                amount_cents=1000,
                description="payment received",
                currency="eur",
            )

            mock_create.assert_called_once_with(
                "cus_abc",
                amount=-1000,
                currency="eur",
                description="payment received",
            )
            assert result["amount_cents"] == 1000  # flipped back for admin display

    def test_negative_amount_sends_positive_to_stripe(self):
        """Admin debits org -500 → Stripe gets +500 (they owe us)."""
        fake_tx = SimpleNamespace(
            id="txn_2",
            amount=500,
            currency="eur",
            description="manual charge",
            created=1_700_000_001,
            type="adjustment",
        )
        with patch.object(stripe_helper, "STRIPE_ENABLED", True), \
             patch.object(stripe_helper.stripe.Customer, "create_balance_transaction",
                          return_value=fake_tx) as mock_create:
            result = stripe_helper.adjust_org_balance(
                stripe_customer_id="cus_abc",
                amount_cents=-500,
                description="manual charge",
                currency="eur",
            )

            mock_create.assert_called_once_with(
                "cus_abc",
                amount=500,
                currency="eur",
                description="manual charge",
            )
            assert result["amount_cents"] == -500

    def test_zero_amount_rejected(self):
        with patch.object(stripe_helper, "STRIPE_ENABLED", True):
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc:
                stripe_helper.adjust_org_balance("cus_abc", 0, "noop", currency="eur")
            assert exc.value.status_code == 400


class TestGetOrgBalance:
    """get_org_balance flips Stripe's sign for admin display."""

    def test_credit_shown_as_positive(self):
        """Stripe balance of -10000 (credit) surfaces as +10000 for admin."""
        fake_customer = {"balance": -10000, "currency": "eur"}
        with patch.object(stripe_helper, "STRIPE_ENABLED", True), \
             patch.object(stripe_helper.stripe.Customer, "retrieve", return_value=fake_customer):
            result = stripe_helper.get_org_balance("cus_abc")
            assert result["balance_cents"] == 10000
            assert result["currency"] == "eur"

    def test_debt_shown_as_negative(self):
        """Stripe balance of +5000 (owed) surfaces as -5000 for admin."""
        fake_customer = {"balance": 5000, "currency": "eur"}
        with patch.object(stripe_helper, "STRIPE_ENABLED", True), \
             patch.object(stripe_helper.stripe.Customer, "retrieve", return_value=fake_customer):
            result = stripe_helper.get_org_balance("cus_abc")
            assert result["balance_cents"] == -5000


class TestRunBillingCycle:
    """run_billing_cycle debits due orgs and advances their cycle."""

    def test_debits_and_advances_due_org(self):
        """An org past its cycle end gets debited and its cycle rolls forward."""
        from src.tasks import billing

        now = datetime(2026, 5, 1, 3, 0, 0)
        cycle_start = datetime(2026, 4, 1, 3, 0, 0)
        cycle_end = datetime(2026, 5, 1, 3, 0, 0)

        org = MagicMock()
        org.id = 42
        org.stripe_id = "cus_abc"
        org.billing_price_id = "price_x"
        org.billing_cycle_started_at = cycle_start
        org.billing_cycle_end = cycle_end

        fake_session = MagicMock()

        with patch.object(stripe_helper, "is_enabled", return_value=True), \
             patch.object(billing, "SessionLocal", return_value=fake_session), \
             patch.object(billing, "get_orgs_due_for_cycle_debit", return_value=[org]), \
             patch.object(stripe_helper, "get_price_details",
                          return_value={"amount": 3000, "currency": "eur", "interval": "month",
                                        "name": "Pro", "price_id": "price_x", "seats": 10}), \
             patch.object(stripe_helper, "adjust_org_balance") as mock_adjust, \
             patch.object(billing, "log_event"):
            processed = billing.run_billing_cycle(now=now)

        assert processed == 1
        mock_adjust.assert_called_once()
        kwargs = mock_adjust.call_args.kwargs
        assert kwargs["amount_cents"] == -3000  # debit (admin-signed)
        assert kwargs["stripe_customer_id"] == "cus_abc"
        # Cycle rolls forward one interval from the old cycle_end
        assert org.billing_cycle_started_at == cycle_end
        assert org.billing_cycle_end == cycle_end + timedelta(days=30)
        fake_session.commit.assert_called_once()

    def test_skips_org_without_stripe_id(self):
        """Orgs with an assigned plan but no Stripe customer are skipped."""
        from src.tasks import billing

        org = MagicMock()
        org.id = 43
        org.stripe_id = None
        org.billing_price_id = "price_x"

        fake_session = MagicMock()
        with patch.object(stripe_helper, "is_enabled", return_value=True), \
             patch.object(billing, "SessionLocal", return_value=fake_session), \
             patch.object(billing, "get_orgs_due_for_cycle_debit", return_value=[org]), \
             patch.object(stripe_helper, "adjust_org_balance") as mock_adjust:
            processed = billing.run_billing_cycle(now=datetime(2026, 5, 1))

        assert processed == 0
        mock_adjust.assert_not_called()
