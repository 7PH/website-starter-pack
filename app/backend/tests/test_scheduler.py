# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
"""Cluster-singleton cron runs: the advisory lock must be taken and released on the same connection."""

from unittest.mock import MagicMock, patch

from src.tasks import _scheduler


def _connection(got_lock: bool) -> MagicMock:
    conn = MagicMock()
    conn.execute.return_value.scalar.return_value = got_lock
    return conn


def _run(conn: MagicMock, fn) -> None:
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn
    with patch.object(_scheduler, "engine", engine):
        _scheduler._run_once_per_cluster(42, "test", fn)


def _statements(conn: MagicMock) -> list[str]:
    return [str(call.args[0]) for call in conn.execute.call_args_list]


def test_lock_and_unlock_on_the_same_connection_every_tick():
    """A Session would hand its connection back on commit and unlock on another one, leaving the lock held for good."""
    fn = MagicMock()
    for _ in range(2):
        conn = _connection(got_lock=True)
        _run(conn, fn)
        assert _statements(conn) == [
            "SELECT pg_try_advisory_lock(:lock_id)",
            "SELECT pg_advisory_unlock(:lock_id)",
        ]
    assert fn.call_count == 2


def test_skips_when_another_worker_holds_the_lock():
    fn = MagicMock()
    conn = _connection(got_lock=False)
    _run(conn, fn)
    fn.assert_not_called()
    assert _statements(conn) == ["SELECT pg_try_advisory_lock(:lock_id)"]


def test_unlocks_even_when_the_job_fails():
    conn = _connection(got_lock=True)
    _run(conn, MagicMock(side_effect=RuntimeError("boom")))
    assert "SELECT pg_advisory_unlock(:lock_id)" in _statements(conn)
