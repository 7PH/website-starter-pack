# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Scheduled tasks module.
Provides periodic background tasks using fastapi-utils.

Usage:
    from .tasks import register_core_tasks

    # In main.py, after app creation:
    register_core_tasks(app)
"""

from .backups import register_backup_tasks
from .cleanup import register_cleanup_tasks


def register_core_tasks(app):
    """
    Register all core scheduled tasks with the FastAPI app.
    Call this after creating the app instance.
    """
    register_cleanup_tasks(app)
    register_backup_tasks(app)
