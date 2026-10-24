# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Backup controller for database backup management.
"""

import gzip
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from ..constants import CMS_ENABLED
from ..helpers.auth import get_current_admin
from ..helpers.logging import get_logger
from ..schemas.backup import BackupInfo, BackupListResponse, BackupTag, RestoreRequest
from ..schemas.user import UserRead

router = APIRouter(prefix="/admin/backups")
logger = get_logger(__name__)

BACKUP_DIR = Path("/app/backups")
MAX_BACKUPS = 7
# CMS uploads only (CMS_ENABLED), never the whole static dir: some apps keep many GB there.
CMS_MEDIA_DIR = Path("/app/static/cms")
DB_PREFIX = "db_backup_"
MEDIA_PREFIX = "cms_media_"

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


def media_path(db_filename: str) -> Path:
    """Media archive paired with a DB backup: same timestamp and tag, different prefix."""
    stem = db_filename.removeprefix(DB_PREFIX).removesuffix(".sql.gz")
    return BACKUP_DIR / f"{MEDIA_PREFIX}{stem}.tar.gz"


def _backup_info(filepath: Path) -> BackupInfo:
    stat = filepath.stat()
    media = media_path(filepath.name)
    media_size = media.stat().st_size if CMS_ENABLED and media.exists() else None
    return BackupInfo(
        filename=filepath.name,
        size=stat.st_size,
        created_at=datetime.fromtimestamp(stat.st_mtime),
        comment=parse_backup_comment(filepath.name),
        media_filename=media.name if media_size is not None else None,
        media_size=media_size,
    )


def _pg_env() -> tuple[dict[str, str], str, str, str]:
    """Return (subprocess env, host, user, db_name) sourced from APP_DB_* vars."""
    env = {
        **os.environ,
        "PGPASSWORD": os.environ.get("APP_DB_PASSWORD") or "",
    }
    return (
        env,
        os.environ.get("APP_DB_HOST", "db"),
        os.environ.get("APP_DB_USER", ""),
        os.environ.get("APP_DB_NAME", ""),
    )


def get_backup_files() -> list[BackupInfo]:
    """Get list of backup files with metadata, newest first."""
    if not BACKUP_DIR.exists():
        return []
    backups = [_backup_info(f) for f in BACKUP_DIR.glob("db_backup_*.sql.gz")]
    return sorted(backups, key=lambda b: b.created_at, reverse=True)


def cleanup_old_backups(keep: str | None = None) -> None:
    """Remove backups exceeding MAX_BACKUPS retention, never the `keep` filename (a backup being restored)."""
    backups = get_backup_files()
    for old_backup in backups[MAX_BACKUPS:]:
        if old_backup.filename == keep:
            continue
        filepath = BACKUP_DIR / old_backup.filename
        filepath.unlink(missing_ok=True)
        media_path(old_backup.filename).unlink(missing_ok=True)
        logger.info(f"Removed old backup: {old_backup.filename}")


def run_backup(tag: BackupTag | None = None, keep: str | None = None) -> BackupInfo:
    """Execute the backup and return the new backup info. `keep` is spared by retention."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    suffix = f"_{tag}" if tag else ""
    filepath = BACKUP_DIR / f"db_backup_{timestamp}{suffix}.sql.gz"

    env, db_host, db_user, db_name = _pg_env()
    with gzip.open(filepath, "wb") as dst, tempfile.TemporaryFile() as errfile:
        proc = subprocess.Popen(
            ["pg_dump", "-h", db_host, "-U", db_user, db_name],
            stdout=subprocess.PIPE,
            stderr=errfile,
            env=env,
        )
        shutil.copyfileobj(proc.stdout, dst)
        proc.stdout.close()
        returncode = proc.wait()
        errfile.seek(0)
        stderr = errfile.read().decode(errors="replace")
    if returncode != 0:
        filepath.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup failed: {stderr}",
        )

    # After the dump: an upload in between leaves an unused folder, never a page pointing at a missing photo.
    if CMS_ENABLED:
        backup_media(media_path(filepath.name))

    cleanup_old_backups(keep=keep)
    return _backup_info(filepath)


def backup_media(dest: Path) -> None:
    """Archive the CMS media folder. Written under a temp name so a failed run never pairs a half archive."""
    part = dest.with_name(dest.name + ".part")
    try:
        with tarfile.open(part, "w:gz") as tar:
            # An empty archive still pairs, so restoring it empties the folder to match the DB.
            if CMS_MEDIA_DIR.exists():
                tar.add(CMS_MEDIA_DIR, arcname=".")
        part.rename(dest)
    except OSError as e:
        # Keep the DB backup: a media problem must not cost the nightly DB backup.
        part.unlink(missing_ok=True)
        logger.error(f"CMS media backup failed: {e}")


def extract_media(archive: Path) -> Path:
    """Extract a media archive into a work dir next to the media folder and return it. Raises 500 if unreadable."""
    CMS_MEDIA_DIR.parent.mkdir(parents=True, exist_ok=True)
    # Same filesystem as the target, so the renames in swap_media are atomic (a /tmp dir may be another mount).
    work = Path(tempfile.mkdtemp(dir=CMS_MEDIA_DIR.parent, prefix=".cms-restore-"))
    try:
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(work / "new", filter="data")
        (work / "new").mkdir(exist_ok=True)
    except (OSError, tarfile.TarError) as e:
        shutil.rmtree(work, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CMS media archive unreadable: {e}",
        ) from e
    return work


def swap_media(work: Path) -> None:
    """Put the extracted media in place of the current folder, then drop the old one."""
    old_dir = work / "old"
    if CMS_MEDIA_DIR.exists():
        CMS_MEDIA_DIR.rename(old_dir)
    try:
        (work / "new").rename(CMS_MEDIA_DIR)
    except OSError:
        # Work dir is kept: if the rollback below fails too, it holds the only copy of the current photos.
        logger.error(f"CMS media swap failed, work dir left in place: {work}")
        if old_dir.exists() and not CMS_MEDIA_DIR.exists():
            old_dir.rename(CMS_MEDIA_DIR)
        raise
    shutil.rmtree(work, ignore_errors=True)


def validate_backup_filename(filename: str, allow_media: bool = False) -> Path:
    """Validate filename and return resolved path, or raise 400/404. Media archives are only accepted where asked."""
    prefixes = (DB_PREFIX, MEDIA_PREFIX) if allow_media and CMS_ENABLED else (DB_PREFIX,)
    if "/" in filename or "\\" in filename or not filename.startswith(prefixes):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")

    filepath = BACKUP_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found")

    return filepath


def run_restore(filepath: Path) -> None:
    """Drop all public tables and restore from a gzipped backup."""
    env, db_host, db_user, db_name = _pg_env()
    # Read the whole dump before dropping anything: a missing or corrupt file must not leave an empty DB.
    try:
        with gzip.open(filepath, "rb") as src:
            while src.read(1024 * 1024):
                pass
    except (OSError, EOFError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup file unreadable: {e}",
        ) from e

    drop_sql = (
        "DO $$ DECLARE r RECORD; BEGIN "
        "FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP "
        "EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE'; "
        "END LOOP; END $$;"
    )
    result = subprocess.run(
        ["psql", "-h", db_host, "-U", db_user, "-d", db_name, "-c", drop_sql],
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to drop tables: {result.stderr}",
        )

    with gzip.open(filepath, "rb") as src, tempfile.TemporaryFile() as errfile:
        proc = subprocess.Popen(
            ["psql", "-h", db_host, "-U", db_user, "-d", db_name],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=errfile,
            env=env,
        )
        shutil.copyfileobj(src, proc.stdin)
        proc.stdin.close()
        returncode = proc.wait()
        errfile.seek(0)
        stderr = errfile.read().decode(errors="replace")
    if returncode != 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Restore failed: {stderr}",
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
    """Download a backup file (DB dump or CMS media archive)."""
    filepath = validate_backup_filename(filename, allow_media=True)

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
    media_path(filename).unlink(missing_ok=True)
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
    safety_backup = run_backup(tag=BackupTag.prerestore, keep=filename)
    if CMS_ENABLED and safety_backup.media_filename is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the current CMS photos, restore aborted",
        )

    # Extracted before touching the DB, so a corrupt archive aborts the whole restore.
    media = media_path(filename)
    media_work = extract_media(media) if CMS_ENABLED and media.exists() else None

    # Restore
    logger.info(f"Restoring database from {filename} (admin {admin.id})")
    try:
        run_restore(filepath)
    except Exception:
        if media_work:
            shutil.rmtree(media_work, ignore_errors=True)
        raise
    if media_work:
        swap_media(media_work)
    logger.info(f"Database restored from {filename} (admin {admin.id}, safety backup: {safety_backup.filename})")

    return safety_backup
