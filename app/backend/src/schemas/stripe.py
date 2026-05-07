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
    cancel_at_period_end: bool = False


class WebhookResponse(BaseModel):
    """Response from webhook endpoint (internal use only)."""
    status: str


class StripePlan(BaseModel):
    """Available individual-user subscription plan (one entry per USER_STRIPE_PRICE_IDS)."""

    price_id: str
    name: str
    amount: int
    currency: str
    interval: str  # month, year, week, day


class StripeCheckoutRequest(BaseModel):
    """Body for POST /stripe/checkout."""

    price_id: str


class StripeCheckoutResponse(BaseModel):
    """Response from POST /stripe/checkout."""

    url: str
