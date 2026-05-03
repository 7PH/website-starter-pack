# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Stripe integration helper.
Provides functions for customer management, billing portal, and webhook handling.
"""

import logging
import os
from collections.abc import Callable
from datetime import datetime, timedelta

import stripe
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Default status dicts for subscriptions (avoid duplication)
_DEFAULT_USER_SUB_STATUS: dict = {
    "is_premium": False,
    "plan": None,
    "expires_at": None,
    "cancel_at_period_end": False,
}
_DEFAULT_ORG_SUB_STATUS: dict = {
    "stripe_premium": False,
    "stripe_quota": 0,
    "expires_at": None,
    "cancel_at_period_end": False,
}

# Configuration
STRIPE_ENABLED = bool(os.environ.get("STRIPE_API_KEY"))
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICING_FREE = os.environ.get("STRIPE_PRICING_FREE", "")


def init_stripe():
    """Initialize Stripe with API key. Call this at app startup."""
    if STRIPE_ENABLED:
        stripe.api_key = STRIPE_API_KEY
        logger.info("Stripe initialized")


def is_enabled() -> bool:
    """Check if Stripe is configured."""
    return STRIPE_ENABLED


def sync_org_customer(
    org_id: int,
    email: str,
    name: str,
    existing_stripe_id: str | None = None,
) -> str:
    """
    Sync an organization to Stripe as a customer.
    Creates a new customer if none exists, or updates the existing one.

    Args:
        org_id: Internal organization ID
        email: Organization's email
        name: Organization's name
        existing_stripe_id: Existing Stripe customer ID if any

    Returns:
        Stripe customer ID
    """
    if not STRIPE_ENABLED:
        logger.warning("Stripe not enabled, skipping org customer sync")
        return ""

    try:
        if existing_stripe_id:
            # Update existing customer
            customer = stripe.Customer.modify(
                existing_stripe_id,
                email=email,
                name=name,
                metadata={"org_id": str(org_id)},
            )
            return customer.id

        # Create new customer for organization
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={"org_id": str(org_id)},
        )
        return customer.id

    except stripe.error.StripeError as e:
        logger.error(f"Stripe org customer sync error: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync with payment provider") from e


def get_price_details(price_id: str) -> dict | None:
    """
    Get price details from Stripe including product name and seats from metadata.

    Args:
        price_id: Stripe price ID

    Returns:
        Dict with price_id, name, amount, currency, seats or None if not found/error
    """
    if not STRIPE_ENABLED:
        return None

    try:
        price = stripe.Price.retrieve(price_id, expand=["product"])
        product = price.product

        # Get product name
        product_name = product.name if hasattr(product, "name") else "Unknown Plan"

        # Get seats from price metadata (fallback to 0)
        try:
            seats = int(price.metadata.get("seats", 0)) if price.metadata else 0
        except (ValueError, TypeError):
            seats = 0

        # Get billing interval (month, year, etc.)
        interval = price.recurring.interval if price.recurring else "month"

        return {
            "price_id": price.id,
            "name": product_name,
            "amount": price.unit_amount or 0,
            "currency": price.currency,
            "seats": seats,
            "interval": interval,
        }

    except stripe.error.StripeError as e:
        logger.warning(f"Stripe price fetch error for {price_id}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Unexpected error fetching price {price_id}: {e}")
        return None


def sync_customer(
    user_id: int,
    email: str,
    name: str,
    existing_stripe_id: str | None = None,
    check_user_exists: Callable[[int], bool] | None = None,
) -> str:
    """
    Sync a user to Stripe as a customer.
    Creates a new customer if none exists, or updates the existing one.
    Will reuse an orphaned customer (linked to deleted user) if found.

    Args:
        user_id: Internal user ID
        email: User's email
        name: User's display name
        existing_stripe_id: Existing Stripe customer ID if any
        check_user_exists: Optional callback to check if a user ID exists in the database.
                          Required to enable orphaned customer reuse.

    Returns:
        Stripe customer ID
    """
    if not STRIPE_ENABLED:
        logger.warning("Stripe not enabled, skipping customer sync")
        return ""

    try:
        if existing_stripe_id:
            # Update existing customer
            customer = stripe.Customer.modify(
                existing_stripe_id,
                email=email,
                name=name,
                metadata={"user_id": str(user_id)},
            )
            return customer.id

        # Search for existing customer by email that we can reuse
        existing = stripe.Customer.list(email=email, limit=1)
        if existing.data:
            candidate = existing.data[0]
            linked_user_id = candidate.metadata.get("user_id")

            # Only reuse if customer has our metadata, user no longer exists, and we can check
            if linked_user_id and check_user_exists is not None:
                try:
                    if not check_user_exists(int(linked_user_id)):
                        # Orphaned customer - safe to reuse
                        stripe.Customer.modify(
                            candidate.id,
                            name=name,
                            metadata={"user_id": str(user_id)},
                        )
                        logger.info(f"Reused orphaned Stripe customer {candidate.id}")
                        return candidate.id
                except (ValueError, TypeError):
                    pass  # Invalid linked_user_id, skip reuse

        # Create new customer (default path)
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={"user_id": str(user_id)},
        )
        return customer.id

    except stripe.error.StripeError as e:
        logger.error(f"Stripe customer sync error: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync with payment provider") from e


def create_subscription(
    stripe_customer_id: str,
    price_id: str | None = None,
) -> str | None:
    """
    Create a subscription for a customer.

    Args:
        stripe_customer_id: Stripe customer ID
        price_id: Stripe price ID (defaults to STRIPE_PRICING_FREE)

    Returns:
        Subscription ID if created, None otherwise
    """
    if not STRIPE_ENABLED:
        return None

    price = price_id or STRIPE_PRICING_FREE
    if not price:
        logger.debug("No price ID configured, skipping subscription creation")
        return None

    try:
        subscription = stripe.Subscription.create(
            customer=stripe_customer_id,
            items=[{"price": price}],
        )
        logger.info(f"Created subscription {subscription.id} for customer {stripe_customer_id}")
        return subscription.id

    except stripe.error.StripeError as e:
        logger.error(f"Stripe subscription error: {e}")
        return None


def has_active_subscription(stripe_customer_id: str) -> bool:
    """
    Check if a customer has any active subscription.

    Args:
        stripe_customer_id: Stripe customer ID

    Returns:
        True if customer has at least one active subscription
    """
    if not STRIPE_ENABLED or not stripe_customer_id:
        return False

    try:
        subscriptions = stripe.Subscription.list(
            customer=stripe_customer_id,
            status="active",
            limit=1,
        )
        return len(subscriptions.data) > 0

    except stripe.error.StripeError as e:
        logger.error(f"Stripe subscription check error: {e}")
        return False


def create_billing_portal_session(
    stripe_customer_id: str,
    return_url: str,
) -> str:
    """
    Create a Stripe billing portal session for the customer.

    Args:
        stripe_customer_id: Stripe customer ID
        return_url: URL to return to after portal session

    Returns:
        Billing portal session URL
    """
    if not STRIPE_ENABLED:
        raise HTTPException(status_code=500, detail="Payment provider not configured")

    if not stripe_customer_id:
        raise HTTPException(status_code=400, detail="No payment account linked")

    try:
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=return_url,
        )
        return session.url

    except stripe.error.StripeError as e:
        logger.error(f"Stripe billing portal error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create billing portal session") from e


def create_checkout_session(
    stripe_customer_id: str,
    price_id: str,
    success_url: str,
    cancel_url: str,
) -> str:
    """
    Create a Stripe checkout session for subscription.

    Args:
        stripe_customer_id: Stripe customer ID
        price_id: Stripe price ID for the subscription
        success_url: URL to redirect on success
        cancel_url: URL to redirect on cancel

    Returns:
        Checkout session URL
    """
    if not STRIPE_ENABLED:
        raise HTTPException(status_code=500, detail="Payment provider not configured")

    try:
        session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session.url

    except stripe.error.StripeError as e:
        logger.error(f"Stripe checkout error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session") from e


def verify_webhook_signature(payload: bytes, signature: str) -> dict:
    """
    Verify and parse a Stripe webhook event.

    Args:
        payload: Raw request body
        signature: Stripe-Signature header

    Returns:
        Parsed webhook event

    Raises:
        HTTPException if signature is invalid
    """
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload, signature, STRIPE_WEBHOOK_SECRET
        )
        return event

    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook signature") from e


def _parse_subscription(sub) -> dict:
    """
    Parse a Stripe subscription and extract common status fields.

    Returns dict with:
        - is_premium: bool - whether subscription has non-zero price
        - price_id: str | None - the price ID
        - seats: int - seats from price metadata (for org subscriptions)
        - cancel_at_period_end: bool
        - expires_at: str | None - ISO date if subscription is canceling
    """
    # Fetch subscription items
    sub_items = stripe.SubscriptionItem.list(subscription=sub.id)
    items_list = list(sub_items.auto_paging_iter())

    price_id = items_list[0].price.id if items_list else None

    # Check if this is a paid subscription and get seats
    is_premium = False
    seats = 0
    for item in items_list:
        if item.price.unit_amount and item.price.unit_amount > 0:
            is_premium = True
            if item.price.metadata:
                try:
                    seats = int(item.price.metadata.get("seats", 0))
                except (ValueError, TypeError):
                    seats = 0
            break

    # Check if subscription is scheduled to cancel
    cancel_at_period_end = getattr(sub, "cancel_at_period_end", False) or False

    # Get expiry date when subscription is canceling
    expires_at = None
    if cancel_at_period_end and sub.cancel_at:
        expires_at = datetime.fromtimestamp(sub.cancel_at).isoformat()

    return {
        "is_premium": is_premium,
        "price_id": price_id,
        "seats": seats,
        "cancel_at_period_end": cancel_at_period_end,
        "expires_at": expires_at,
    }


def _fetch_active_subscription(stripe_customer_id: str) -> dict | None:
    """Return the first active subscription parsed via :func:`_parse_subscription`, or None."""
    if not STRIPE_ENABLED or not stripe_customer_id:
        return None
    try:
        subscriptions = stripe.Subscription.list(
            customer=stripe_customer_id,
            status="active",
            limit=1,
        )
        for sub in subscriptions.auto_paging_iter():
            return _parse_subscription(sub)
    except stripe.error.StripeError as e:
        logger.error(f"Stripe subscription check error: {e}")
    return None


def get_subscription_status(stripe_customer_id: str) -> dict:
    """Return is_premium / plan / expires_at / cancel_at_period_end for a user."""
    parsed = _fetch_active_subscription(stripe_customer_id)
    if not parsed:
        return _DEFAULT_USER_SUB_STATUS.copy()
    return {
        "is_premium": parsed["is_premium"],
        "plan": parsed["price_id"],
        "expires_at": parsed["expires_at"],
        "cancel_at_period_end": parsed["cancel_at_period_end"],
    }


def get_org_subscription_status(stripe_customer_id: str) -> dict:
    """Return stripe_premium / stripe_quota / expires_at / cancel_at_period_end for an org."""
    parsed = _fetch_active_subscription(stripe_customer_id)
    if not parsed:
        return _DEFAULT_ORG_SUB_STATUS.copy()
    return {
        "stripe_premium": parsed["is_premium"],
        "stripe_quota": parsed["seats"],
        "expires_at": parsed["expires_at"],
        "cancel_at_period_end": parsed["cancel_at_period_end"],
    }


# ---------------------------------------------------------------------------
# Customer balance (admin-managed billing ledger)
#
# Stripe's customer.balance convention: negative = customer has credit,
# positive = customer owes. That's counterintuitive for admin UI, so every
# helper below flips the sign at the boundary. In Python-land: positive =
# credit (they've paid us), negative = owed (they're behind). See
# https://docs.stripe.com/invoicing/customer/balance.
# ---------------------------------------------------------------------------


def get_org_balance(stripe_customer_id: str) -> dict:
    """Return the org's running balance + currency (admin sign convention)."""
    if not STRIPE_ENABLED or not stripe_customer_id:
        return {"balance_cents": 0, "currency": "eur"}

    try:
        customer = stripe.Customer.retrieve(stripe_customer_id)
        return {
            "balance_cents": -int(customer.get("balance", 0) or 0),
            "currency": customer.get("currency") or "eur",
        }
    except stripe.error.StripeError as e:
        logger.error(f"Stripe balance fetch error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch balance") from e


def adjust_org_balance(
    stripe_customer_id: str,
    amount_cents: int,
    description: str,
    currency: str | None = None,
) -> dict:
    """Record a balance change. Positive = credit them, negative = charge them."""
    if not STRIPE_ENABLED or not stripe_customer_id:
        raise HTTPException(status_code=500, detail="Payment provider not configured")

    if amount_cents == 0:
        raise HTTPException(status_code=400, detail="Amount cannot be zero")

    try:
        resolved_currency = currency
        if not resolved_currency:
            customer = stripe.Customer.retrieve(stripe_customer_id)
            resolved_currency = customer.get("currency") or "eur"

        tx = stripe.Customer.create_balance_transaction(
            stripe_customer_id,
            amount=-amount_cents,
            currency=resolved_currency,
            description=description,
        )
        return {
            "id": tx.id,
            "amount_cents": -int(tx.amount),
            "currency": tx.currency,
            "description": tx.description,
            "created_at": datetime.fromtimestamp(tx.created).isoformat(),
            "type": tx.type,
        }
    except stripe.error.StripeError as e:
        logger.error(f"Stripe balance adjustment error: {e}")
        raise HTTPException(status_code=500, detail="Failed to adjust balance") from e


def list_org_balance_transactions(stripe_customer_id: str, limit: int = 50) -> list[dict]:
    """Return recent balance transactions, newest first, with flipped sign."""
    if not STRIPE_ENABLED or not stripe_customer_id:
        return []

    try:
        txs = stripe.Customer.list_balance_transactions(stripe_customer_id, limit=limit)
        return [
            {
                "id": tx.id,
                "amount_cents": -int(tx.amount),
                "currency": tx.currency,
                "description": tx.description,
                "created_at": datetime.fromtimestamp(tx.created).isoformat(),
                "type": tx.type,
            }
            for tx in txs.data
        ]
    except stripe.error.StripeError as e:
        logger.error(f"Stripe balance transaction list error: {e}")
        return []


def get_dashboard_customer_url(stripe_customer_id: str) -> str | None:
    """Return the Stripe dashboard URL for a customer, or None if Stripe isn't configured."""
    if not stripe_customer_id or not STRIPE_API_KEY:
        return None
    prefix = "test/" if STRIPE_API_KEY.startswith("sk_test_") else ""
    return f"https://dashboard.stripe.com/{prefix}customers/{stripe_customer_id}"


def compute_next_cycle_end(interval: str, from_ts: datetime, interval_count: int = 1) -> datetime:
    """Advance a billing cycle boundary by one interval."""
    count = max(1, int(interval_count or 1))
    if interval == "day":
        return from_ts + timedelta(days=count)
    if interval == "week":
        return from_ts + timedelta(weeks=count)
    if interval == "year":
        return from_ts.replace(year=from_ts.year + count)
    # Default: month. Approximate one month as 30 days — keeps things deterministic
    # and avoids the pitfalls of end-of-month arithmetic (e.g. Jan 31 + 1 month).
    return from_ts + timedelta(days=30 * count)
