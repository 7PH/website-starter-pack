# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Stripe API endpoints.
Provides billing portal access and webhook handling.
"""

import logging

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from ..constants import ORG_STRIPE_PRICE_IDS
from ..crud.organizations import get_organization_by_stripe_id, reset_org_members_premium, update_organization
from ..crud.users import (
    get_user_by_id,
    get_user_by_stripe_id,
    update_user,
    update_user_premium_cache,
)
from ..helpers import stripe as stripe_helper
from ..helpers.auth import get_current_nonmanaged_user, get_user_or_404
from ..helpers.db import SessionLocal, get_session
from ..schemas.stripe import BillingPortalResponse, SubscriptionStatus, WebhookResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stripe", tags=["Stripe"])


@router.get("/portal", response_model=BillingPortalResponse)
def get_billing_portal(
    return_url: str = Query(..., description="URL to return to after portal session"),
    user=Depends(get_current_nonmanaged_user),
    session: Session = Depends(get_session),
):
    """
    Get a Stripe billing portal URL for the current user.
    Allows users to manage their subscription, update payment methods, etc.
    Creates a Stripe customer if one doesn't exist.
    """
    db_user = get_user_or_404(session, user.id)

    # Create Stripe customer if user doesn't have one
    if not db_user.stripe_id:
        db_user.stripe_id = stripe_helper.sync_customer(
            user_id=user.id,
            email=user.email,
            name=f"{user.first_name} {user.last_name}",
            check_user_exists=lambda uid: get_user_by_id(session, uid) is not None,
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


@router.get("/subscription", response_model=SubscriptionStatus)
def get_subscription_status(
    user=Depends(get_current_nonmanaged_user),
    session: Session = Depends(get_session),
):
    """
    Get the current user's subscription status.
    Always queries Stripe API for accuracy and syncs DB if status differs.
    """
    db_user = get_user_by_id(session, user.id)

    if not db_user:
        return SubscriptionStatus(is_premium=False, plan=None, expires_at=None)

    # Always query Stripe for current status and sync DB
    if db_user.stripe_id:
        stripe_status = stripe_helper.get_subscription_status(db_user.stripe_id)

        # Sync DB if personal subscription status differs (handles webhook failures)
        if stripe_status["is_premium"] != db_user.has_personal_subscription:
            db_user.has_personal_subscription = stripe_status["is_premium"]
            session.commit()
            update_user_premium_cache(session, db_user.id)

        return SubscriptionStatus(**stripe_status)

    return SubscriptionStatus(is_premium=False, plan=None, expires_at=None)


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


def _subscription_items(subscription: dict) -> list[dict]:
    return subscription.get("items", {}).get("data", [])


def _is_premium_subscription(subscription: dict) -> bool:
    """Check if a subscription is for a premium plan (vs free)."""
    if subscription.get("status") not in ("active", "trialing"):
        return False
    # Premium iff any item has a non-zero unit price.
    return any(item.get("price", {}).get("unit_amount", 0) > 0 for item in _subscription_items(subscription))


def _get_subscription_price_id(subscription: dict) -> str | None:
    items = _subscription_items(subscription)
    return items[0].get("price", {}).get("id") if items else None


def _get_seats_from_subscription(subscription: dict) -> int:
    items = _subscription_items(subscription)
    if not items:
        return 0
    metadata = items[0].get("price", {}).get("metadata", {})
    try:
        return int(metadata.get("seats", 0))
    except (ValueError, TypeError):
        return 0


def _is_org_subscription(price_id: str | None) -> bool:
    """Check if a price ID is for an organization subscription."""
    return price_id is not None and price_id in ORG_STRIPE_PRICE_IDS


def _apply_user_premium(session: Session, customer_id: str, has_subscription: bool) -> None:
    user = get_user_by_stripe_id(session, customer_id)
    if not user:
        logger.warning(f"No user found for Stripe customer {customer_id}")
        return
    user.has_personal_subscription = has_subscription
    session.commit()
    update_user_premium_cache(session, user.id)
    logger.info(f"Updated user {user.id} has_personal_subscription={has_subscription}")


def _apply_org_subscription(session: Session, customer_id: str, is_premium: bool, seats: int) -> None:
    org = get_organization_by_stripe_id(session, customer_id)
    if not org:
        logger.warning(f"No org found for Stripe customer {customer_id}")
        return
    org.stripe_premium = is_premium
    org.stripe_quota = seats if is_premium else 0
    update_organization(session, org)
    logger.info(f"Updated org {org.id} premium={is_premium} quota={seats}")
    if not is_premium:
        affected_user_ids = reset_org_members_premium(session, org.id)
        for user_id in affected_user_ids:
            update_user_premium_cache(session, user_id)
        logger.info(f"Cleared {len(affected_user_ids)} premium seats for org {org.id}")


def _apply_subscription_event(event: dict, action: str, *, is_premium: bool | None = None) -> None:
    """Route a subscription webhook event to the user or org updater.

    ``action`` is the verb used in the log line (created/updated/deleted).
    Pass ``is_premium=False`` to force a deletion-style update without inspecting the payload.
    """
    subscription = event.get("data", {}).get("object", {})
    customer_id = subscription.get("customer")
    if not customer_id:
        logger.warning("Webhook event missing customer ID")
        return

    price_id = _get_subscription_price_id(subscription)
    deleting = is_premium is False
    effective_premium = False if deleting else _is_premium_subscription(subscription)

    session = SessionLocal()
    try:
        if _is_org_subscription(price_id):
            seats = 0 if deleting else _get_seats_from_subscription(subscription)
            logger.info(f"Org subscription {action}: premium={effective_premium}, seats={seats}")
            _apply_org_subscription(session, customer_id, effective_premium, seats)
        else:
            logger.info(f"User subscription {action}: premium={effective_premium}")
            _apply_user_premium(session, customer_id, effective_premium)
    except Exception as e:
        logger.error(f"Error processing subscription {action}: {e}")
        session.rollback()
    finally:
        session.close()


def _handle_subscription_created(event: dict):
    _apply_subscription_event(event, "created")


def _handle_subscription_updated(event: dict):
    _apply_subscription_event(event, "updated")


def _handle_subscription_deleted(event: dict):
    _apply_subscription_event(event, "deleted", is_premium=False)


def _handle_payment_succeeded(_event: dict):
    """Handle successful payment."""
    pass


def _handle_payment_failed(_event: dict):
    """Handle failed payment."""
    pass
