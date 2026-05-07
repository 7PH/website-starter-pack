# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Stripe API endpoints.

Provides individual-user billing portal, checkout, and webhook handling.
The webhook fires ``SubscriptionChanged`` (helpers/hooks.py) so sub-apps
can persist tier metadata, audit logs, etc. in the same transaction as
the starterpack's own ``is_premium`` update.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from ..constants import ORG_STRIPE_PRICE_IDS, PUBLIC_URL, STRIPE_ENABLED, USER_STRIPE_PRICE_IDS
from ..crud.organizations import get_organization_by_stripe_id, reset_org_members_premium, update_organization
from ..crud.users import (
    get_user_by_id,
    get_user_by_stripe_id,
    update_user_premium_cache,
)
from ..helpers import stripe as stripe_helper
from ..helpers.auth import get_current_nonmanaged_user, get_user_or_404
from ..helpers.db import get_session
from ..helpers.hooks import SubscriptionChanged, fire
from ..helpers.redirects import validate_redirect_url
from ..models.organization import OrganizationBase
from ..models.user import UserBase
from ..schemas.stripe import (
    BillingPortalResponse,
    StripeCheckoutRequest,
    StripeCheckoutResponse,
    StripePlan,
    SubscriptionStatus,
    WebhookResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stripe", tags=["Stripe"])


# ─── plans ───


@router.get("/plans", response_model=list[StripePlan])
def get_user_plans():
    """Return the list of plans available for individual user subscriptions.

    Driven by ``USER_STRIPE_PRICE_IDS``. Returns an empty list when Stripe
    is disabled or no price IDs are configured (the frontend hides the
    Subscribe button in that case).
    """
    if not STRIPE_ENABLED or not stripe_helper.is_enabled():
        return []
    if not USER_STRIPE_PRICE_IDS:
        return []
    plans: list[StripePlan] = []
    for price_id in USER_STRIPE_PRICE_IDS:
        details = stripe_helper.get_price_details(price_id)
        if details:
            plans.append(
                StripePlan(
                    price_id=details["price_id"],
                    name=details["name"],
                    amount=details["amount"],
                    currency=details["currency"],
                    interval=details["interval"],
                    metadata=details.get("metadata", {}),
                )
            )
    return plans


# ─── portal ───


@router.get("/portal", response_model=BillingPortalResponse)
def get_billing_portal(
    return_url: str = Query(..., description="URL to return to after portal session"),
    user=Depends(get_current_nonmanaged_user),
    session: Session = Depends(get_session),
):
    """Open the Stripe billing portal for the current user.

    Returns 400 when the user has no active subscription — the frontend
    sends them through ``POST /stripe/checkout`` first. The starterpack
    no longer auto-creates a $0 shell subscription on first portal open
    (removed in v3.4.0).
    """
    db_user = get_user_or_404(session, user.id)

    if not db_user.stripe_id or not stripe_helper.has_active_subscription(db_user.stripe_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription. Use POST /stripe/checkout to subscribe.",
        )

    validated_url = validate_redirect_url(return_url, PUBLIC_URL)
    if not validated_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid return URL")

    url = stripe_helper.create_billing_portal_session(
        stripe_customer_id=db_user.stripe_id,
        return_url=validated_url,
    )
    return BillingPortalResponse(url=url)


# ─── checkout ───


@router.post("/checkout", response_model=StripeCheckoutResponse)
def create_user_checkout(
    *,
    request: Request,
    user=Depends(get_current_nonmanaged_user),
    session: Session = Depends(get_session),
    body: StripeCheckoutRequest,
):
    """Create a Stripe checkout session for an individual subscription.

    The ``price_id`` must be in ``USER_STRIPE_PRICE_IDS`` (allowlist
    prevents arbitrary-price checkout). On success the user is redirected
    to Stripe-hosted checkout; the webhook flips ``is_premium`` once
    payment completes.
    """
    if not STRIPE_ENABLED or not stripe_helper.is_enabled():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Billing not enabled")
    if body.price_id not in USER_STRIPE_PRICE_IDS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid price ID")

    db_user = get_user_or_404(session, user.id)

    if not db_user.stripe_id:
        db_user.stripe_id = stripe_helper.sync_customer(
            user_id=user.id,
            email=user.email,
            name=f"{user.first_name} {user.last_name}",
            check_user_exists=lambda uid: get_user_by_id(session, uid) is not None,
        )
        session.add(db_user)
        session.commit()

    origin = request.headers.get("origin", "")
    public_url = PUBLIC_URL or validate_redirect_url(origin) or ""
    if not public_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid origin for redirect")
    success_url = f"{public_url}/account?subscription=success"
    cancel_url = f"{public_url}/account?subscription=canceled"

    url = stripe_helper.create_checkout_session(
        stripe_customer_id=db_user.stripe_id,
        price_id=body.price_id,
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return StripeCheckoutResponse(url=url)


# ─── subscription status ───


@router.get("/subscription", response_model=SubscriptionStatus)
def get_subscription_status(
    user=Depends(get_current_nonmanaged_user),
    session: Session = Depends(get_session),
):
    """Read current subscription status, syncing the DB if Stripe disagrees.

    Hits the Stripe API every call (no caching) so the UI always reflects
    the source of truth — webhook drops mid-deploy or local-dev clock skew
    can otherwise leave the DB row stale.
    """
    db_user = get_user_by_id(session, user.id)

    if not db_user:
        return SubscriptionStatus(is_premium=False, plan=None, expires_at=None)

    if db_user.stripe_id:
        stripe_status = stripe_helper.get_subscription_status(db_user.stripe_id)
        if stripe_status["is_premium"] != db_user.has_personal_subscription:
            db_user.has_personal_subscription = stripe_status["is_premium"]
            session.commit()
            update_user_premium_cache(session, db_user.id)
        return SubscriptionStatus(**stripe_status)

    return SubscriptionStatus(is_premium=False, plan=None, expires_at=None)


# ─── webhook ───


@router.post("/webhook", response_model=WebhookResponse, include_in_schema=False)
async def stripe_webhook(
    request: Request,
    session: Session = Depends(get_session),
):
    """Handle Stripe webhooks.

    All event handling shares one request-scoped session so the
    starterpack's own writes and any app-side ``SubscriptionChanged``
    handler writes commit atomically. ``get_session`` doesn't auto-commit
    on success, so this endpoint commits explicitly at the end.

    Idempotency note: Stripe may deliver the same event more than once.
    The starterpack's own writes are idempotent in shape; app handlers
    must be too.
    """
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")

    event = stripe_helper.verify_webhook_signature(payload, signature)
    event_type = event.get("type", "")

    if event_type == "customer.subscription.created":
        _apply_subscription_event(session, event, action="created")
    elif event_type == "customer.subscription.updated":
        _apply_subscription_event(session, event, action="updated")
    elif event_type == "customer.subscription.deleted":
        _apply_subscription_event(session, event, action="deleted", is_premium=False)
    elif event_type == "invoice.payment_succeeded" or event_type == "invoice.payment_failed":
        pass

    session.commit()
    return WebhookResponse(status="success")


# ─── webhook helpers ───


def _subscription_items(subscription: dict) -> list[dict]:
    return subscription.get("items", {}).get("data", [])


def _is_premium_subscription(subscription: dict) -> bool:
    """Premium iff any line item has unit_amount > 0 and the sub is active/trialing."""
    if subscription.get("status") not in ("active", "trialing"):
        return False
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
    return price_id is not None and price_id in ORG_STRIPE_PRICE_IDS


def _apply_user_premium(session: Session, customer_id: str, has_subscription: bool) -> UserBase | None:
    user = get_user_by_stripe_id(session, customer_id)
    if not user:
        logger.warning(f"No user found for Stripe customer {customer_id}")
        return None
    user.has_personal_subscription = has_subscription
    session.flush()
    update_user_premium_cache(session, user.id)
    logger.info(f"Updated user {user.id} has_personal_subscription={has_subscription}")
    return user


def _apply_org_subscription(
    session: Session,
    customer_id: str,
    is_premium: bool,
    seats: int,
) -> OrganizationBase | None:
    org = get_organization_by_stripe_id(session, customer_id)
    if not org:
        logger.warning(f"No org found for Stripe customer {customer_id}")
        return None
    org.stripe_premium = is_premium
    org.stripe_quota = seats if is_premium else 0
    update_organization(session, org)
    logger.info(f"Updated org {org.id} premium={is_premium} quota={seats}")
    if not is_premium:
        affected_user_ids = reset_org_members_premium(session, org.id)
        for user_id in affected_user_ids:
            update_user_premium_cache(session, user_id)
        logger.info(f"Cleared {len(affected_user_ids)} premium seats for org {org.id}")
    return org


def _apply_subscription_event(
    session: Session,
    event: dict,
    *,
    action: str,
    is_premium: bool | None = None,
) -> None:
    """Apply the starterpack's own writes for a subscription event, then fire ``SubscriptionChanged``.

    ``action`` is the verb used in log lines (``created`` / ``updated`` /
    ``deleted``). Pass ``is_premium=False`` to force a deletion-style
    update without inspecting the payload.
    """
    subscription = event.get("data", {}).get("object", {})
    customer_id = subscription.get("customer")
    if not customer_id:
        logger.warning("Webhook event missing customer ID")
        return

    price_id = _get_subscription_price_id(subscription)
    deleting = is_premium is False
    effective_premium = False if deleting else _is_premium_subscription(subscription)

    resolved_user: UserBase | None = None
    resolved_org: OrganizationBase | None = None
    if _is_org_subscription(price_id):
        seats = 0 if deleting else _get_seats_from_subscription(subscription)
        logger.info(f"Org subscription {action}: premium={effective_premium}, seats={seats}")
        resolved_org = _apply_org_subscription(session, customer_id, effective_premium, seats)
    else:
        logger.info(f"User subscription {action}: premium={effective_premium}")
        resolved_user = _apply_user_premium(session, customer_id, effective_premium)

    fire(
        session,
        SubscriptionChanged(
            action=action,  # type: ignore[arg-type]
            raw_event=event,
            user=resolved_user,
            organization=resolved_org,
        ),
    )
