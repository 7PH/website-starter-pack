# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Shared lifecycle wiring for module-level APScheduler instances."""

from collections.abc import Callable
from dataclasses import dataclass
from functools import partial

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text

from ..helpers.db import engine
from ..helpers.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class _ScheduledJob:
    scheduler: AsyncIOScheduler
    func: Callable
    cron: CronTrigger
    job_id: str
    log_name: str


_REGISTERED: list[_ScheduledJob] = []


def _run_once_per_cluster(lock_id: int, log_name: str, fn: Callable) -> None:
    """Run `fn` only if we win a Postgres session-level advisory lock.

    Use when running uvicorn with >1 worker (BACKEND_WORKERS>1), or when scaling
    backend pods horizontally. All workers tick the cron at the same moment;
    only the worker that grabs the lock executes. The lock auto-releases when
    the connection closes, so a crashed worker won't hold it past the run.

    `lock_id` must be a stable 64-bit signed int. Pick a hand-chosen constant
    per job (no random/hash) so the lock identity is consistent across deploys.

    Holds one pool connection for the duration of `fn()`. For our daily jobs
    that's a few seconds at 4am, which is fine; if you add a long-running
    cluster-singleton job that runs during peak traffic, size DB_POOL_SIZE
    accordingly.
    """
    # A Connection, not a Session: a Session hands its connection back to the pool on commit, so the unlock would run
    # on another connection and the lock would stay held by an idle pooled one, skipping every later tick.
    try:
        with engine.connect() as conn:
            got_lock = conn.execute(text("SELECT pg_try_advisory_lock(:lock_id)"), {"lock_id": lock_id}).scalar()
            # Ends the implicit transaction, or the connection sits "idle in transaction" for the whole job and
            # DB_IDLE_IN_TRANSACTION_TIMEOUT_MS kills it mid-run. The advisory lock is session-level and survives.
            conn.commit()
            if not got_lock:
                logger.debug(f"{log_name}: another worker holds the cluster lock; skipping this tick")
                return
            try:
                fn()
            finally:
                try:
                    conn.execute(text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": lock_id})
                    conn.commit()
                except Exception:
                    # Connection went bad: the pool must discard it rather than hand a still-locked one back out.
                    # The lock dies when the backend closes the connection.
                    conn.invalidate()
                    raise
    except Exception as e:
        logger.error(f"{log_name}: cluster-singleton execution failed: {e}", exc_info=True)


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

    # FastAPI ignores on_event handlers when the app sets `lifespan=`, so jobs are
    # collected here and the lifespan starts them.
    _REGISTERED.append(_ScheduledJob(scheduler, effective_job_func, cron, job_id, log_name))


def start_scheduled_tasks() -> None:
    """Start every scheduler registered so far. Called from main.py's lifespan."""
    for job in _REGISTERED:
        job.scheduler.add_job(job.func, job.cron, id=job.job_id, replace_existing=True)
        if not job.scheduler.running:
            job.scheduler.start()
        logger.info(f"{job.log_name} scheduler started")


def stop_scheduled_tasks() -> None:
    for job in _REGISTERED:
        if job.scheduler.running:
            job.scheduler.shutdown()
            logger.info(f"{job.log_name} scheduler stopped")
