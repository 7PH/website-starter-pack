# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Scheduled backup tasks using APScheduler for cron-style scheduling.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ..controllers.backups import run_backup
from ..helpers.logging import get_logger
from ..schemas.backup import BackupTag

logger = get_logger(__name__)

scheduler = AsyncIOScheduler()


def scheduled_backup():
    """Run scheduled database backup."""
    try:
        logger.info("Starting scheduled backup")
        backup = run_backup(tag=BackupTag.automatic)
        logger.info(f"Scheduled backup completed: {backup.filename}")
    except Exception as e:
        logger.error(f"Scheduled backup failed: {e}")


def register_backup_tasks(app):
    from . import CORE_LOCK_ID_BACKUP, DAILY_BACKUP_HOUR
    from ._scheduler import register_cron_task

    register_cron_task(
        app,
        scheduler,
        job_func=scheduled_backup,
        cron=CronTrigger(hour=DAILY_BACKUP_HOUR, minute=0),
        job_id="daily_backup",
        log_name="Backup",
        cluster_lock_id=CORE_LOCK_ID_BACKUP,
    )
