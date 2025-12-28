# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Stripe API endpoints.
Provides billing portal access and webhook handling.
"""

from fastapi import APIRouter, Request, Depends, Query
from pydantic import BaseModel

from ..helpers.auth import get_current_user
from ..helpers import stripe as stripe_helper

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
):
    """
    Get a Stripe billing portal URL for the current user.
    Allows users to manage their subscription, update payment methods, etc.
    """
    if not hasattr(user, "stripe_id") or not user.stripe_id:
        # If user doesn't have a Stripe ID yet, we could create one here
        # For now, return an error
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No payment account linked")

    url = stripe_helper.create_billing_portal_session(
        stripe_customer_id=user.stripe_id,
        return_url=return_url,
    )

    return BillingPortalResponse(url=url)


@router.get("/subscription")
def get_subscription_status(
    user=Depends(get_current_user),
):
    """
    Get the current user's subscription status.
    """
    if not hasattr(user, "stripe_id") or not user.stripe_id:
        return {"is_premium": False, "plan": None, "expires_at": None}

    return stripe_helper.get_subscription_status(user.stripe_id)


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


def _handle_subscription_created(event: dict):
    """Handle new subscription creation."""
    # Override this in your project to update user premium status
    pass


def _handle_subscription_updated(event: dict):
    """Handle subscription updates."""
    # Override this in your project to update user premium status
    pass


def _handle_subscription_deleted(event: dict):
    """Handle subscription cancellation."""
    # Override this in your project to remove user premium status
    pass


def _handle_payment_succeeded(event: dict):
    """Handle successful payment."""
    pass


def _handle_payment_failed(event: dict):
    """Handle failed payment."""
    pass
