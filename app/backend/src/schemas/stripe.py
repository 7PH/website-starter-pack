# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Stripe-related Pydantic schemas."""

from pydantic import BaseModel, Field


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
    """Available individual-user subscription plan (one entry per USER_STRIPE_PRICE_IDS).

    ``metadata`` is a passthrough of the Stripe price's metadata dict.
    Apps can label plans with arbitrary keys (tier, seat quota, feature
    flags) and read them off ``plan.metadata`` on the frontend without
    duplicating data via env vars.
    """

    price_id: str
    name: str
    amount: int
    currency: str
    interval: str  # month, year, week, day
    metadata: dict[str, str] = Field(default_factory=dict)


class StripeCheckoutRequest(BaseModel):
    """Body for POST /stripe/checkout."""

    price_id: str


class StripeCheckoutResponse(BaseModel):
    """Response from POST /stripe/checkout."""

    url: str
