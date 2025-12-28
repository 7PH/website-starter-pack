# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Stripe integration helper.
Provides functions for customer management, billing portal, and webhook handling.
"""

import os
import logging
from typing import Optional
from datetime import datetime

import stripe
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Configuration
STRIPE_ENABLED = bool(os.environ.get("STRIPE_API_KEY"))
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# Optional pricing IDs for subscription plans
STRIPE_PRICING_FREE = os.environ.get("STRIPE_PRICING_FREE", "")
STRIPE_PRICING_PREMIUM_MONTHLY = os.environ.get("STRIPE_PRICING_PREMIUM_MONTHLY", "")
STRIPE_PRICING_PREMIUM_YEARLY = os.environ.get("STRIPE_PRICING_PREMIUM_YEARLY", "")


def init_stripe():
    """Initialize Stripe with API key. Call this at app startup."""
    if STRIPE_ENABLED:
        stripe.api_key = STRIPE_API_KEY
        logger.info("Stripe initialized")


def is_enabled() -> bool:
    """Check if Stripe is configured."""
    return STRIPE_ENABLED


def sync_customer(
    user_id: int,
    email: str,
    name: str,
    existing_stripe_id: Optional[str] = None,
) -> str:
    """
    Sync a user to Stripe as a customer.
    Creates a new customer if none exists, or updates the existing one.

    Args:
        user_id: Internal user ID
        email: User's email
        name: User's display name
        existing_stripe_id: Existing Stripe customer ID if any

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
        else:
            # Create new customer
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={"user_id": str(user_id)},
            )

        return customer.id

    except stripe.error.StripeError as e:
        logger.error(f"Stripe customer sync error: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync with payment provider")


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
        raise HTTPException(status_code=500, detail="Failed to create billing portal session")


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
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


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
        raise HTTPException(status_code=400, detail="Invalid webhook signature")


def get_subscription_status(stripe_customer_id: str) -> dict:
    """
    Get the subscription status for a customer.

    Args:
        stripe_customer_id: Stripe customer ID

    Returns:
        Dict with is_premium, plan, and expires_at
    """
    if not STRIPE_ENABLED or not stripe_customer_id:
        return {"is_premium": False, "plan": None, "expires_at": None}

    try:
        subscriptions = stripe.Subscription.list(
            customer=stripe_customer_id,
            status="active",
            limit=1,
        )

        if subscriptions.data:
            sub = subscriptions.data[0]
            return {
                "is_premium": True,
                "plan": sub.items.data[0].price.id if sub.items.data else None,
                "expires_at": datetime.fromtimestamp(sub.current_period_end),
            }

        return {"is_premium": False, "plan": None, "expires_at": None}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe subscription check error: {e}")
        return {"is_premium": False, "plan": None, "expires_at": None}
