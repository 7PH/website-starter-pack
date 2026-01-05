# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Scheduled backup tasks using APScheduler for cron-style scheduling.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ..controllers.backups import run_backup
from ..helpers.logging import get_logger

logger = get_logger(__name__)

scheduler = AsyncIOScheduler()


def scheduled_backup():
    """Run scheduled database backup."""
    try:
        logger.info("Starting scheduled backup")
        backup = run_backup()
        logger.info(f"Scheduled backup completed: {backup.filename}")
    except Exception as e:
        logger.error(f"Scheduled backup failed: {e}")


def register_backup_tasks(app):
    """Register backup scheduled tasks with the FastAPI app."""

    @app.on_event("startup")
    async def start_backup_scheduler():
        # Schedule daily backup at 4:00 AM
        scheduler.add_job(
            scheduled_backup,
            CronTrigger(hour=4, minute=0),
            id="daily_backup",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("Backup scheduler started (daily at 4:00 AM)")

    @app.on_event("shutdown")
    async def stop_backup_scheduler():
        scheduler.shutdown()
        logger.info("Backup scheduler stopped")
