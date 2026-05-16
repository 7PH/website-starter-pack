# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Shared lifecycle wiring for module-level APScheduler instances."""

from collections.abc import Callable
from functools import partial

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text

from ..helpers.db import SessionLocal
from ..helpers.logging import get_logger

logger = get_logger(__name__)


def _run_once_per_cluster(lock_id: int, log_name: str, fn: Callable) -> None:
    """Run `fn` only if we win a Postgres session-level advisory lock.

    Use when running uvicorn with >1 worker (BACKEND_WORKERS>1), or when scaling
    backend pods horizontally. All workers tick the cron at the same moment;
    only the worker that grabs the lock executes. The lock auto-releases when
    the session disconnects, so a crashed worker won't hold it past the run.

    `lock_id` must be a stable 64-bit signed int. Pick a hand-chosen constant
    per job (no random/hash) so the lock identity is consistent across deploys.

    Holds one pool connection for the duration of `fn()`. For our daily jobs
    that's a few seconds at 4am, which is fine; if you add a long-running
    cluster-singleton job that runs during peak traffic, size DB_POOL_SIZE
    accordingly.
    """
    session = SessionLocal()
    try:
        got_lock = session.execute(text("SELECT pg_try_advisory_lock(:lock_id)"), {"lock_id": lock_id}).scalar()
        # Close the implicit transaction SQLAlchemy opened for the SELECT above.
        # Without this commit, the lock session is "idle in transaction" for the
        # whole job, which DB_IDLE_IN_TRANSACTION_TIMEOUT_MS would kill,
        # releasing the lock mid-run. The advisory lock itself is session-level
        # and survives the commit.
        session.commit()
        if not got_lock:
            logger.debug(f"{log_name}: another worker holds the cluster lock; skipping this tick")
            return
        try:
            fn()
        finally:
            try:
                session.execute(text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": lock_id})
                session.commit()
            except Exception:
                # Connection went bad. Invalidate it so the pool discards it
                # instead of handing the still-locked connection back out.
                # The lock dies when the backend closes the connection.
                session.invalidate()
                raise
    except Exception as e:
        logger.error(f"{log_name}: cluster-singleton execution failed: {e}", exc_info=True)
    finally:
        session.close()


def register_cron_task(
    app,
    scheduler: AsyncIOScheduler,
    *,
    job_func: Callable,
    cron: CronTrigger,
    job_id: str,
    log_name: str,
    cluster_lock_id: int | None = None,
) -> None:
    """Register start/stop lifecycle hooks for a scheduler with one cron job.

    If `cluster_lock_id` is set, the job is wrapped in `_run_once_per_cluster`
    so only one worker / pod runs it per tick. Omit for per-worker jobs (e.g.
    in-memory cache cleanup).
    """

    if cluster_lock_id is not None:
        effective_job_func = partial(_run_once_per_cluster, cluster_lock_id, log_name, job_func)
    else:
        effective_job_func = job_func

    @app.on_event("startup")
    async def _start():
        scheduler.add_job(effective_job_func, cron, id=job_id, replace_existing=True)
        scheduler.start()
        logger.info(f"{log_name} scheduler started")

    @app.on_event("shutdown")
    async def _stop():
        scheduler.shutdown()
        logger.info(f"{log_name} scheduler stopped")
