# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Shared lifecycle wiring for module-level APScheduler instances."""

from collections.abc import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ..helpers.logging import get_logger

logger = get_logger(__name__)


def register_cron_task(
    app,
    scheduler: AsyncIOScheduler,
    *,
    job_func: Callable,
    cron: CronTrigger,
    job_id: str,
    log_name: str,
) -> None:
    """Register start/stop lifecycle hooks for a scheduler with one cron job."""

    @app.on_event("startup")
    async def _start():
        scheduler.add_job(job_func, cron, id=job_id, replace_existing=True)
        scheduler.start()
        logger.info(f"{log_name} scheduler started")

    @app.on_event("shutdown")
    async def _stop():
        scheduler.shutdown()
        logger.info(f"{log_name} scheduler stopped")
