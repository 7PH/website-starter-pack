# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Stripe API endpoints.
Provides billing portal access and webhook handling.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
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
from ..helpers.auth import get_current_user
from ..helpers.db import SessionLocal, get_session
from ..schemas.stripe import BillingPortalResponse, SubscriptionStatus, WebhookResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stripe", tags=["Stripe"])


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
    user=Depends(get_current_user),
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


def _get_subscription_price_id(subscription: dict) -> str | None:
    """Extract the price ID from a subscription."""
    items = subscription.get("items", {}).get("data", [])
    if items:
        return items[0].get("price", {}).get("id")
    return None


def _get_seats_from_subscription(subscription: dict) -> int:
    """Extract the seats from price metadata."""
    items = subscription.get("items", {}).get("data", [])
    if items:
        price = items[0].get("price", {})
        metadata = price.get("metadata", {})
        try:
            return int(metadata.get("seats", 0))
        except (ValueError, TypeError):
            return 0
    return 0


def _is_org_subscription(price_id: str | None) -> bool:
    """Check if a price ID is for an organization subscription."""
    return price_id is not None and price_id in ORG_STRIPE_PRICE_IDS


def _update_user_premium_from_event(event: dict, has_subscription: bool) -> None:
    """Update user personal subscription status from a webhook event."""
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
            user.has_personal_subscription = has_subscription
            session.commit()
            update_user_premium_cache(session, user.id)
            logger.info(f"Updated user {user.id} has_personal_subscription={has_subscription}")
        else:
            logger.warning(f"No user found for Stripe customer {customer_id}")
    except Exception as e:
        logger.error(f"Error updating user subscription status: {e}")
        session.rollback()
    finally:
        session.close()


def _update_org_subscription_from_event(event: dict, is_premium: bool, seats: int = 0) -> None:
    """Update organization subscription status from a webhook event."""
    data = event.get("data", {})
    subscription = data.get("object", {})
    customer_id = subscription.get("customer")

    if not customer_id:
        logger.warning("Webhook event missing customer ID")
        return

    session = SessionLocal()
    try:
        org = get_organization_by_stripe_id(session, customer_id)
        if org:
            org.stripe_premium = is_premium
            org.stripe_quota = seats if is_premium else 0
            update_organization(session, org)
            logger.info(f"Updated org {org.id} premium={is_premium} quota={seats}")

            # If org subscription is canceled, clear all premium seats using CRUD function
            if not is_premium:
                affected_user_ids = reset_org_members_premium(session, org.id)
                # Update premium cache for all affected users
                for user_id in affected_user_ids:
                    update_user_premium_cache(session, user_id)
                logger.info(f"Cleared {len(affected_user_ids)} premium seats for org {org.id}")
        else:
            logger.warning(f"No org found for Stripe customer {customer_id}")
    except Exception as e:
        logger.error(f"Error updating org subscription status: {e}")
        session.rollback()
    finally:
        session.close()


def _handle_subscription_created(event: dict):
    """Handle new subscription creation."""
    data = event.get("data", {})
    subscription = data.get("object", {})
    price_id = _get_subscription_price_id(subscription)
    is_premium = _is_premium_subscription(subscription)

    if _is_org_subscription(price_id):
        seats = _get_seats_from_subscription(subscription)
        logger.info(f"Org subscription created: premium={is_premium}, seats={seats}")
        _update_org_subscription_from_event(event, is_premium, seats)
    else:
        logger.info(f"User subscription created: premium={is_premium}")
        _update_user_premium_from_event(event, is_premium)


def _handle_subscription_updated(event: dict):
    """Handle subscription updates (plan changes, renewals)."""
    data = event.get("data", {})
    subscription = data.get("object", {})
    price_id = _get_subscription_price_id(subscription)
    is_premium = _is_premium_subscription(subscription)

    if _is_org_subscription(price_id):
        seats = _get_seats_from_subscription(subscription)
        logger.info(f"Org subscription updated: premium={is_premium}, seats={seats}")
        _update_org_subscription_from_event(event, is_premium, seats)
    else:
        logger.info(f"User subscription updated: premium={is_premium}")
        _update_user_premium_from_event(event, is_premium)


def _handle_subscription_deleted(event: dict):
    """Handle subscription cancellation or expiration."""
    data = event.get("data", {})
    subscription = data.get("object", {})
    price_id = _get_subscription_price_id(subscription)

    if _is_org_subscription(price_id):
        logger.info("Org subscription deleted: setting premium=False, quota=0")
        _update_org_subscription_from_event(event, False, 0)
    else:
        logger.info("User subscription deleted: setting premium=False")
        _update_user_premium_from_event(event, False)


def _handle_payment_succeeded(_event: dict):
    """Handle successful payment."""
    pass


def _handle_payment_failed(_event: dict):
    """Handle failed payment."""
    pass
