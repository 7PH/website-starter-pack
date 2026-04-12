# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Backup controller for database backup management.
"""

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from ..helpers.auth import get_current_admin
from ..helpers.logging import get_logger
from ..schemas.backup import BackupInfo, BackupListResponse, BackupTag, RestoreRequest
from ..schemas.user import UserRead

router = APIRouter(prefix="/admin/backups")
logger = get_logger(__name__)

BACKUP_DIR = Path("/app/backups")
MAX_BACKUPS = 7

# Filename format: db_backup_YYYY-MM-DD_HH-MM-SS[_tag].sql.gz
BACKUP_FILENAME_RE = re.compile(r"^db_backup_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(?:_([a-z]+))?.sql.gz$")

TAG_COMMENTS: dict[BackupTag, str] = {
    BackupTag.automatic: "Automatic backup",
    BackupTag.manual: "Manual backup",
    BackupTag.prerestore: "Pre-restore backup",
}


def parse_backup_comment(filename: str) -> str | None:
    """Extract the tag from a backup filename and return its human-readable comment."""
    match = BACKUP_FILENAME_RE.match(filename)
    if not match or not match.group(1):
        return None
    try:
        tag = BackupTag(match.group(1))
    except ValueError:
        return match.group(1)
    return TAG_COMMENTS[tag]


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
                comment=parse_backup_comment(file.name),
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


def run_backup(tag: BackupTag | None = None) -> BackupInfo:
    """Execute the backup and return the new backup info."""
    # Create backup directory if needed
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    suffix = f"_{tag}" if tag else ""
    filename = f"db_backup_{timestamp}{suffix}.sql.gz"
    filepath = BACKUP_DIR / filename

    # Get database credentials from environment
    db_name = os.environ.get("APP_DB_NAME")
    db_user = os.environ.get("APP_DB_USER")
    db_password = os.environ.get("APP_DB_PASSWORD")
    db_host = os.environ.get("APP_DB_HOST", "db")

    # Run pg_dump and compress with gzip
    cmd = f"pg_dump -h {db_host} -U {db_user} {db_name} | gzip > {filepath}"
    env = {**os.environ, "PGPASSWORD": db_password or ""}

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
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
        comment=parse_backup_comment(filename),
    )


def validate_backup_filename(filename: str) -> Path:
    """Validate filename and return resolved path, or raise 400/404."""
    if "/" in filename or "\\" in filename or not filename.startswith("db_backup_"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")

    filepath = BACKUP_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found")

    return filepath


def run_restore(filepath: Path) -> None:
    """Drop all public tables and restore from a gzipped backup."""
    db_name = os.environ.get("APP_DB_NAME")
    db_user = os.environ.get("APP_DB_USER")
    db_password = os.environ.get("APP_DB_PASSWORD")
    db_host = os.environ.get("APP_DB_HOST", "db")
    env = {**os.environ, "PGPASSWORD": db_password or ""}

    # Drop all tables in the public schema
    drop_sql = (
        "DO $$ DECLARE r RECORD; BEGIN "
        "FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP "
        "EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE'; "
        "END LOOP; END $$;"
    )
    result = subprocess.run(
        ["psql", "-h", db_host, "-U", db_user, "-d", db_name, "-c", drop_sql],
        capture_output=True, text=True, env=env,
    )
    if result.returncode != 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to drop tables: {result.stderr}",
        )

    # Restore from gzipped backup
    cmd = f"gunzip -c {filepath} | psql -h {db_host} -U {db_user} -d {db_name}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Restore failed: {result.stderr}",
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
    return run_backup(tag=BackupTag.manual)


@router.get("/{filename}")
def get_backup(
    filename: str,
    admin: UserRead = Depends(get_current_admin),
):
    """Download a backup file."""
    filepath = validate_backup_filename(filename)

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
    filepath = validate_backup_filename(filename)

    filepath.unlink()
    logger.info(f"Backup deleted by admin {admin.id}: {filename}")


@router.post("/{filename}/restore", response_model=BackupInfo)
def restore_backup(
    filename: str,
    body: RestoreRequest,
    admin: UserRead = Depends(get_current_admin),
):
    """Restore database from a backup. Creates a safety backup first."""
    filepath = validate_backup_filename(filename)

    # Double-check: body confirmation must match URL filename
    if body.confirm_filename != filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation filename does not match",
        )

    # Create pre-restore safety backup
    logger.info(f"Creating pre-restore backup before restoring {filename} (admin {admin.id})")
    safety_backup = run_backup(tag=BackupTag.prerestore)

    # Restore
    logger.info(f"Restoring database from {filename} (admin {admin.id})")
    run_restore(filepath)
    logger.info(f"Database restored from {filename} (admin {admin.id}, safety backup: {safety_backup.filename})")

    return safety_backup
