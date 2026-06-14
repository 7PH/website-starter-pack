# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Cleanup tasks for periodic maintenance.

Rate-limit cleanup used to live here; it moved to Redis key TTLs when the
limiter became Redis-backed, so there are no periodic cleanup tasks right now.
This hook stays as the registration point for future ones.
"""


def register_cleanup_tasks(app):
    """Register periodic cleanup tasks with the FastAPI app. Currently none."""
    return
