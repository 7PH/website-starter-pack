# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Tests for backups, with and without the CMS media archive (CMS_ENABLED)."""

import gzip
import io
import os
import tarfile
from unittest.mock import MagicMock

os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")
os.environ.setdefault("TOKEN_HASH_SECRET", "test-secret-not-for-prod")

import pytest
from fastapi import HTTPException

from src.controllers import backups
from src.schemas.backup import BackupTag, RestoreRequest

ADMIN = MagicMock(id=1)


@pytest.fixture
def dirs(tmp_path, monkeypatch):
    """Point backups and CMS media at temp dirs and fake pg_dump/psql."""
    backup_dir = tmp_path / "backups"
    media_dir = tmp_path / "static" / "cms"
    (media_dir / "media" / "1").mkdir(parents=True)
    (media_dir / "media" / "1" / "480.webp").write_bytes(b"photo")
    monkeypatch.setattr(backups, "BACKUP_DIR", backup_dir)
    monkeypatch.setattr(backups, "CMS_MEDIA_DIR", media_dir)

    def fake_popen(*args, **kwargs):
        proc = MagicMock()
        proc.stdout = io.BytesIO(b"-- dump")
        proc.wait.return_value = 0
        return proc

    monkeypatch.setattr(backups.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(backups.subprocess, "run", MagicMock(return_value=MagicMock(returncode=0)))
    return backup_dir, media_dir


@pytest.fixture
def cms_on(monkeypatch):
    monkeypatch.setattr(backups, "CMS_ENABLED", True)


@pytest.fixture
def cms_off(monkeypatch):
    monkeypatch.setattr(backups, "CMS_ENABLED", False)


def _make_db_backup(backup_dir, stamp: str, mtime: int, media: bool = False) -> str:
    backup_dir.mkdir(exist_ok=True)
    name = f"db_backup_{stamp}_automatic.sql.gz"
    (backup_dir / name).write_bytes(gzip.compress(b"db", mtime=0))
    os.utime(backup_dir / name, (mtime, mtime))
    if media:
        (backup_dir / f"cms_media_{stamp}_automatic.tar.gz").write_bytes(b"media")
    return name


class TestFlagOff:
    def test_backup_writes_db_dump_only(self, dirs, cms_off):
        backup_dir, _ = dirs
        info = backups.run_backup(tag=BackupTag.manual)
        assert [p.name for p in backup_dir.iterdir()] == [info.filename]
        assert info.media_filename is None
        assert info.media_size is None

    def test_listing_output_is_unchanged(self, dirs, cms_off):
        backup_dir, _ = dirs
        # A leftover archive from when CMS was on must not show up either.
        _make_db_backup(backup_dir, "2026-01-01_04-00-00", 1000, media=True)
        [item] = backups.list_backups(admin=ADMIN).items
        assert item.model_dump(exclude={"created_at"}) == {
            "filename": "db_backup_2026-01-01_04-00-00_automatic.sql.gz",
            "size": (backup_dir / item.filename).stat().st_size,
            "comment": "Automatic backup",
            "media_filename": None,
            "media_size": None,
        }

    def test_media_archive_not_downloadable(self, dirs, cms_off):
        backup_dir, _ = dirs
        _make_db_backup(backup_dir, "2026-01-01_04-00-00", 1000, media=True)
        with pytest.raises(HTTPException) as exc:
            backups.get_backup("cms_media_2026-01-01_04-00-00_automatic.tar.gz", admin=ADMIN)
        assert exc.value.status_code == 400

    def test_restore_leaves_media_alone(self, dirs, cms_off):
        backup_dir, media_dir = dirs
        name = _make_db_backup(backup_dir, "2026-01-01_04-00-00", 1000, media=True)
        backups.restore_backup(name, RestoreRequest(confirm_filename=name), admin=ADMIN)
        assert (media_dir / "media" / "1" / "480.webp").read_bytes() == b"photo"


class TestRestoreSafety:
    def test_restoring_the_oldest_backup_survives_retention(self, dirs, cms_off, monkeypatch):
        backup_dir, _ = dirs
        monkeypatch.setattr(backups, "MAX_BACKUPS", 2)
        oldest = _make_db_backup(backup_dir, "2026-01-01_04-00-00", 1000)
        _make_db_backup(backup_dir, "2026-01-02_04-00-00", 2000)

        backups.restore_backup(oldest, RestoreRequest(confirm_filename=oldest), admin=ADMIN)

        assert (backup_dir / oldest).exists()

    def test_corrupt_dump_aborts_before_dropping_tables(self, dirs, cms_off):
        backup_dir, _ = dirs
        name = _make_db_backup(backup_dir, "2026-01-01_04-00-00", 1000)
        (backup_dir / name).write_bytes(b"not gzip")
        with pytest.raises(HTTPException):
            backups.restore_backup(name, RestoreRequest(confirm_filename=name), admin=ADMIN)
        backups.subprocess.run.assert_not_called()

    def test_unsaved_current_media_aborts_restore(self, dirs, cms_on, monkeypatch):
        backup_dir, media_dir = dirs
        name = _make_db_backup(backup_dir, "2026-01-01_04-00-00", 1000, media=True)
        monkeypatch.setattr(backups, "backup_media", MagicMock())  # writes nothing, like a full disk
        with pytest.raises(HTTPException):
            backups.restore_backup(name, RestoreRequest(confirm_filename=name), admin=ADMIN)
        backups.subprocess.run.assert_not_called()
        assert (media_dir / "media" / "1" / "480.webp").read_bytes() == b"photo"

    def test_corrupt_media_archive_aborts_before_db(self, dirs, cms_on):
        backup_dir, media_dir = dirs
        name = _make_db_backup(backup_dir, "2026-01-01_04-00-00", 1000, media=True)  # archive is not a tar
        with pytest.raises(HTTPException):
            backups.restore_backup(name, RestoreRequest(confirm_filename=name), admin=ADMIN)
        backups.subprocess.run.assert_not_called()
        assert [p.name for p in media_dir.parent.iterdir()] == ["cms"]


class TestFlagOn:
    def test_backup_pairs_media_archive(self, dirs, cms_on):
        backup_dir, _ = dirs
        info = backups.run_backup(tag=BackupTag.manual)
        stamp = info.filename.removeprefix("db_backup_").removesuffix(".sql.gz")
        assert info.media_filename == f"cms_media_{stamp}.tar.gz"
        assert info.media_size == (backup_dir / info.media_filename).stat().st_size
        with tarfile.open(backup_dir / info.media_filename) as tar:
            assert tar.extractfile("./media/1/480.webp").read() == b"photo"

    def test_missing_media_dir_still_pairs_an_empty_archive(self, dirs, cms_on, tmp_path, monkeypatch):
        monkeypatch.setattr(backups, "CMS_MEDIA_DIR", tmp_path / "nope")
        info = backups.run_backup()
        assert info.media_filename is not None

    def test_media_failure_keeps_db_backup(self, dirs, cms_on, monkeypatch):
        backup_dir, _ = dirs
        monkeypatch.setattr(backups.tarfile, "open", MagicMock(side_effect=OSError("disk full")))
        info = backups.run_backup()
        assert info.media_filename is None
        assert [p.name for p in backup_dir.iterdir()] == [info.filename]

    def test_listing_shows_only_db_rows(self, dirs, cms_on):
        backup_dir, _ = dirs
        _make_db_backup(backup_dir, "2026-01-01_04-00-00", 1000, media=True)
        _make_db_backup(backup_dir, "2026-01-02_04-00-00", 2000)
        items = backups.list_backups(admin=ADMIN).items
        assert [i.media_filename for i in items] == [None, "cms_media_2026-01-01_04-00-00_automatic.tar.gz"]

    def test_retention_deletes_pairs(self, dirs, cms_on, monkeypatch):
        backup_dir, _ = dirs
        monkeypatch.setattr(backups, "MAX_BACKUPS", 1)
        _make_db_backup(backup_dir, "2026-01-01_04-00-00", 1000, media=True)
        _make_db_backup(backup_dir, "2026-01-02_04-00-00", 2000, media=True)
        backups.cleanup_old_backups()
        assert sorted(p.name for p in backup_dir.iterdir()) == [
            "cms_media_2026-01-02_04-00-00_automatic.tar.gz",
            "db_backup_2026-01-02_04-00-00_automatic.sql.gz",
        ]

    def test_delete_removes_pair(self, dirs, cms_on):
        backup_dir, _ = dirs
        name = _make_db_backup(backup_dir, "2026-01-01_04-00-00", 1000, media=True)
        backups.delete_backup(name, admin=ADMIN)
        assert list(backup_dir.iterdir()) == []

    def test_media_archive_downloadable_but_not_deletable_or_restorable(self, dirs, cms_on):
        backup_dir, _ = dirs
        _make_db_backup(backup_dir, "2026-01-01_04-00-00", 1000, media=True)
        media_name = "cms_media_2026-01-01_04-00-00_automatic.tar.gz"
        assert backups.get_backup(media_name, admin=ADMIN).path == backup_dir / media_name
        with pytest.raises(HTTPException):
            backups.delete_backup(media_name, admin=ADMIN)
        with pytest.raises(HTTPException):
            backups.restore_backup(media_name, RestoreRequest(confirm_filename=media_name), admin=ADMIN)

    def test_restore_swaps_media_folder(self, dirs, cms_on):
        backup_dir, media_dir = dirs
        old = backups.run_backup()
        (media_dir / "media" / "2").mkdir()
        (media_dir / "media" / "1" / "480.webp").write_bytes(b"changed")

        backups.restore_backup(old.filename, RestoreRequest(confirm_filename=old.filename), admin=ADMIN)

        assert (media_dir / "media" / "1" / "480.webp").read_bytes() == b"photo"
        assert not (media_dir / "media" / "2").exists()
        # No leftover work dir next to the media folder.
        assert [p.name for p in media_dir.parent.iterdir()] == ["cms"]

    def test_restore_without_pair_leaves_media_alone(self, dirs, cms_on):
        backup_dir, media_dir = dirs
        name = _make_db_backup(backup_dir, "2026-01-01_04-00-00", 1000)
        backups.restore_backup(name, RestoreRequest(confirm_filename=name), admin=ADMIN)
        assert (media_dir / "media" / "1" / "480.webp").read_bytes() == b"photo"
