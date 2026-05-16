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
from .billing import register_billing_tasks
from .cleanup import register_cleanup_tasks

# Daily-cron hours. Billing runs first so debits land before the backup snapshot.
DAILY_BILLING_HOUR = 3
DAILY_BACKUP_HOUR = 4

# Reserved cluster-singleton lock IDs for starterpack-core scheduled jobs
# (see tasks/_scheduler.py::_run_once_per_cluster). 64-bit signed int.
# Sub-apps adding their own cluster-locked jobs should pick IDs OUTSIDE the
# 71500000-71509999 range to avoid collisions on starterpack upgrade.
CORE_LOCK_ID_BACKUP = 71500001
CORE_LOCK_ID_BILLING = 71500002


def register_core_tasks(app):
    """
    Register all core scheduled tasks with the FastAPI app.
    Call this after creating the app instance.
    """
    register_cleanup_tasks(app)
    register_backup_tasks(app)
    register_billing_tasks(app)
