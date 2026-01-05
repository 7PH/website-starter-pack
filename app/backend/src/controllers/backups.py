# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Backup controller for database backup management.
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from ..helpers.auth import get_current_admin
from ..helpers.logging import get_logger
from ..models.backup import BackupInfo, BackupListResponse
from ..models.user import UserRead

router = APIRouter(prefix="/admin/backups")
logger = get_logger(__name__)

BACKUP_DIR = Path("/app/backups")
MAX_BACKUPS = 7


def get_backup_files() -> list[BackupInfo]:
    """Get list of backup files with metadata."""
    if not BACKUP_DIR.exists():
        return []

    backups = []
    for file in BACKUP_DIR.glob("db_backup_*.sql.gz"):
        stat = file.stat()
        backups.append(
            BackupInfo(
                filename=file.name,
                size=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_mtime),
            )
        )

    # Sort by date descending (newest first)
    return sorted(backups, key=lambda b: b.created_at, reverse=True)


def cleanup_old_backups() -> None:
    """Remove backups exceeding MAX_BACKUPS retention."""
    backups = get_backup_files()
    for old_backup in backups[MAX_BACKUPS:]:
        filepath = BACKUP_DIR / old_backup.filename
        filepath.unlink(missing_ok=True)
        logger.info(f"Removed old backup: {old_backup.filename}")


def run_backup() -> BackupInfo:
    """Execute the backup and return the new backup info."""
    # Create backup directory if needed
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"db_backup_{timestamp}.sql.gz"
    filepath = BACKUP_DIR / filename

    # Get database credentials from environment
    db_name = os.environ.get("APP_DB_NAME")
    db_user = os.environ.get("APP_DB_USER")
    db_password = os.environ.get("APP_DB_PASSWORD")
    db_host = os.environ.get("APP_DB_HOST", "db")

    # Run pg_dump and compress with gzip
    cmd = f'PGPASSWORD="{db_password}" pg_dump -h {db_host} -U {db_user} {db_name} | gzip > {filepath}'

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        # Clean up partial file if exists
        filepath.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup failed: {result.stderr}",
        )

    # Cleanup old backups
    cleanup_old_backups()

    stat = filepath.stat()
    return BackupInfo(
        filename=filename,
        size=stat.st_size,
        created_at=datetime.fromtimestamp(stat.st_mtime),
    )


# ============================================================================
# CRUD Endpoints
# ============================================================================


@router.get("", response_model=BackupListResponse)
def list_backups(
    admin: UserRead = Depends(get_current_admin),
):
    """List all database backups."""
    backups = get_backup_files()
    return BackupListResponse(items=backups, total=len(backups))


@router.post("", response_model=BackupInfo, status_code=status.HTTP_201_CREATED)
def create_backup(
    admin: UserRead = Depends(get_current_admin),
):
    """Create a new database backup."""
    logger.info(f"Manual backup triggered by admin {admin.id}")
    return run_backup()


@router.get("/{filename}")
def get_backup(
    filename: str,
    admin: UserRead = Depends(get_current_admin),
):
    """Download a backup file."""
    # Validate filename to prevent path traversal
    if "/" in filename or "\\" in filename or not filename.startswith("db_backup_"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")

    filepath = BACKUP_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found")

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/gzip",
    )


@router.delete("/{filename}", status_code=status.HTTP_204_NO_CONTENT)
def delete_backup(
    filename: str,
    admin: UserRead = Depends(get_current_admin),
):
    """Delete a backup file."""
    # Validate filename to prevent path traversal
    if "/" in filename or "\\" in filename or not filename.startswith("db_backup_"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")

    filepath = BACKUP_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found")

    filepath.unlink()
    logger.info(f"Backup deleted by admin {admin.id}: {filename}")
