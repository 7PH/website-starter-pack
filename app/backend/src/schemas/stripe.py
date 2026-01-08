# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Stripe-related Pydantic schemas."""

from pydantic import BaseModel


class BillingPortalResponse(BaseModel):
    """Response from billing portal endpoint."""
    url: str


class SubscriptionStatus(BaseModel):
    """Current user's subscription status."""
    is_premium: bool
    plan: str | None
    expires_at: str | None


class WebhookResponse(BaseModel):
    """Response from webhook endpoint (internal use only)."""
    status: str
