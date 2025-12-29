# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Stripe API endpoints.
Provides billing portal access and webhook handling.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..crud.users import (
    get_user_by_id,
    get_user_by_stripe_id,
    set_user_premium_status,
    update_user,
)
from ..helpers import stripe as stripe_helper
from ..helpers.auth import get_current_user
from ..helpers.db import SessionLocal, get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stripe", tags=["Stripe"])


class BillingPortalResponse(BaseModel):
    """Response from billing portal endpoint."""
    url: str


class WebhookResponse(BaseModel):
    """Response from webhook endpoint."""
    status: str


@router.get("/portal", response_model=BillingPortalResponse)
def get_billing_portal(
    return_url: str = Query(..., description="URL to return to after portal session"),
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Get a Stripe billing portal URL for the current user.
    Allows users to manage their subscription, update payment methods, etc.
    Creates a Stripe customer if one doesn't exist.
    """
    # Fetch full user from DB to get stripe_id
    db_user = get_user_by_id(session, user.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create Stripe customer if user doesn't have one
    if not db_user.stripe_id:
        db_user.stripe_id = stripe_helper.sync_customer(
            user_id=user.id,
            email=user.email,
            name=f"{user.first_name} {user.last_name}",
        )
        stripe_helper.create_subscription(db_user.stripe_id)
        update_user(session, db_user)
    # Ensure user has an active subscription (create free one if not)
    elif not stripe_helper.has_active_subscription(db_user.stripe_id):
        stripe_helper.create_subscription(db_user.stripe_id)

    url = stripe_helper.create_billing_portal_session(
        stripe_customer_id=db_user.stripe_id,
        return_url=return_url,
    )

    return BillingPortalResponse(url=url)


@router.get("/subscription")
def get_subscription_status(
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Get the current user's subscription status.
    Always queries Stripe API for accuracy and syncs DB if status differs.
    """
    db_user = get_user_by_id(session, user.id)

    if not db_user:
        return {"is_premium": False, "plan": None, "expires_at": None}

    # Always query Stripe for current status and sync DB
    if db_user.stripe_id:
        stripe_status = stripe_helper.get_subscription_status(db_user.stripe_id)

        # Sync DB if status differs (handles webhook failures)
        if stripe_status["is_premium"] != db_user.is_premium:
            set_user_premium_status(session, db_user, stripe_status["is_premium"])

        return stripe_status

    return {"is_premium": False, "plan": None, "expires_at": None}


@router.post("/webhook", response_model=WebhookResponse, include_in_schema=False)
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhooks.
    This endpoint receives events from Stripe about subscription changes, payments, etc.
    """
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")

    event = stripe_helper.verify_webhook_signature(payload, signature)

    # Handle different event types
    event_type = event.get("type", "")

    if event_type == "customer.subscription.created":
        # New subscription created
        _handle_subscription_created(event)

    elif event_type == "customer.subscription.updated":
        # Subscription updated (e.g., plan change, renewal)
        _handle_subscription_updated(event)

    elif event_type == "customer.subscription.deleted":
        # Subscription cancelled or expired
        _handle_subscription_deleted(event)

    elif event_type == "invoice.payment_succeeded":
        # Payment successful
        _handle_payment_succeeded(event)

    elif event_type == "invoice.payment_failed":
        # Payment failed
        _handle_payment_failed(event)

    return WebhookResponse(status="success")


def _is_premium_subscription(subscription: dict) -> bool:
    """Check if a subscription is for a premium plan (vs free)."""
    if subscription.get("status") not in ("active", "trialing"):
        return False

    items = subscription.get("items", {}).get("data", [])
    if not items:
        return False

    # A subscription is premium if any item has a non-zero price
    for item in items:
        price = item.get("price", {})
        unit_amount = price.get("unit_amount", 0)
        if unit_amount > 0:
            return True

    return False


def _update_user_premium_from_event(event: dict, is_premium: bool) -> None:
    """Update user premium status from a webhook event."""
    data = event.get("data", {})
    subscription = data.get("object", {})
    customer_id = subscription.get("customer")

    if not customer_id:
        logger.warning("Webhook event missing customer ID")
        return

    session = SessionLocal()
    try:
        user = get_user_by_stripe_id(session, customer_id)
        if user:
            set_user_premium_status(session, user, is_premium)
            logger.info(f"Updated user {user.id} premium status to {is_premium}")
        else:
            logger.warning(f"No user found for Stripe customer {customer_id}")
    except Exception as e:
        logger.error(f"Error updating user premium status: {e}")
        session.rollback()
    finally:
        session.close()


def _handle_subscription_created(event: dict):
    """Handle new subscription creation."""
    data = event.get("data", {})
    subscription = data.get("object", {})
    is_premium = _is_premium_subscription(subscription)
    logger.info(f"Subscription created: premium={is_premium}")
    _update_user_premium_from_event(event, is_premium)


def _handle_subscription_updated(event: dict):
    """Handle subscription updates (plan changes, renewals)."""
    data = event.get("data", {})
    subscription = data.get("object", {})
    is_premium = _is_premium_subscription(subscription)
    logger.info(f"Subscription updated: premium={is_premium}")
    _update_user_premium_from_event(event, is_premium)


def _handle_subscription_deleted(event: dict):
    """Handle subscription cancellation or expiration."""
    logger.info("Subscription deleted: setting premium=False")
    _update_user_premium_from_event(event, False)


def _handle_payment_succeeded(_event: dict):
    """Handle successful payment."""
    pass


def _handle_payment_failed(_event: dict):
    """Handle failed payment."""
    pass
