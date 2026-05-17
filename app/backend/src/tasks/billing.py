# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Daily billing-cycle debits for orgs with an admin-assigned plan.

We don't create real Stripe subscriptions for these orgs, so Stripe can't
auto-charge them. Instead, each day we find orgs whose cycle has elapsed,
debit the plan amount from their customer balance, and roll the cycle
forward by one interval. Balance can freely go negative (they owe us) —
access is not revoked.
"""

from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ..constants import EventType
from ..crud.event_logs import log_event
from ..crud.organizations import get_orgs_due_for_cycle_debit
from ..helpers import stripe as stripe_helper
from ..helpers.db import SessionLocal
from ..helpers.logging import get_logger

logger = get_logger(__name__)

scheduler = AsyncIOScheduler()


def run_billing_cycle(now: datetime | None = None) -> int:
    """Debit plan amount from every org whose cycle has ended. Returns count processed."""
    if not stripe_helper.is_enabled():
        return 0

    current = now or datetime.now(UTC)
    session = SessionLocal()
    processed = 0
    try:
        orgs = get_orgs_due_for_cycle_debit(session, current)
        for org in orgs:
            if not org.stripe_id:
                logger.warning(f"Org {org.id} has plan assigned but no Stripe customer; skipping")
                continue

            price = stripe_helper.get_price_details(org.billing_price_id)
            if not price:
                logger.warning(f"Could not fetch price {org.billing_price_id} for org {org.id}; skipping")
                continue

            cycle_started = org.billing_cycle_started_at or current
            description = f"Subscription cycle {cycle_started:%Y-%m-%d}"
            # Stable per-cycle key so a re-run after a DB-commit failure
            # reuses Stripe's existing transaction instead of double-charging.
            idempotency_key = f"org-cycle-debit-{org.id}-{cycle_started.isoformat()}"
            try:
                stripe_helper.adjust_org_balance(
                    stripe_customer_id=org.stripe_id,
                    amount_cents=-price["amount"],
                    description=description,
                    currency=price["currency"],
                    idempotency_key=idempotency_key,
                )
            except Exception as e:
                logger.error(f"Failed to debit org {org.id}: {e}")
                continue

            # Commit per-org: Stripe already recorded the debit, so losing the cycle
            # advance to a later rollback would cause a double-charge on the next run.
            org.billing_cycle_started_at = org.billing_cycle_end
            org.billing_cycle_end = stripe_helper.compute_next_cycle_end(
                price["interval"],
                org.billing_cycle_end,
            )
            log_event(
                session,
                action=EventType.ORG_BALANCE_CYCLE_DEBITED,
                user_id=None,
                details={
                    "org_id": org.id,
                    "price_id": org.billing_price_id,
                    "amount_cents": -price["amount"],
                    "cycle_started_at": cycle_started.isoformat(),
                },
            )
            try:
                session.commit()
                processed += 1
            except Exception as e:
                logger.error(f"DB commit failed after Stripe debit for org {org.id}: {e}")
                session.rollback()

        logger.info(f"Billing cycle run complete: {processed} org(s) debited")
        return processed
    except Exception as e:
        logger.error(f"Billing cycle run failed: {e}")
        session.rollback()
        return processed
    finally:
        session.close()


def register_billing_tasks(app):
    from . import CORE_LOCK_ID_BILLING, DAILY_BILLING_HOUR
    from ._scheduler import register_cron_task

    register_cron_task(
        app,
        scheduler,
        job_func=run_billing_cycle,
        cron=CronTrigger(hour=DAILY_BILLING_HOUR, minute=0),
        job_id="daily_billing_cycle",
        log_name="Billing",
        cluster_lock_id=CORE_LOCK_ID_BILLING,
    )
