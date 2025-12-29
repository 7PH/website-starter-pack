# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Cleanup tasks for periodic maintenance.
"""

import logging

from fastapi_utils.tasks import repeat_every

from ..helpers.ratelimit import cleanup_entries as cleanup_ratelimit_entries

logger = logging.getLogger(__name__)


def register_cleanup_tasks(app):
    """
    Register cleanup tasks with the FastAPI app.

    Tasks:
    - Rate limit cleanup: Every 5 minutes
    """

    @app.on_event("startup")
    @repeat_every(wait_first=True, seconds=300)  # Every 5 minutes
    def periodic_ratelimit_cleanup():
        """Clean up expired rate limit entries."""
        try:
            cleanup_ratelimit_entries()
            logger.debug("Rate limit cleanup completed")
        except Exception as e:
            logger.error(f"Rate limit cleanup failed: {e}")
