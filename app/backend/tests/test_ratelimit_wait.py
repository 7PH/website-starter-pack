# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
"""The limiter says how long to wait, so 429s can carry Retry-After (conftest backs it with an in-memory Redis)."""

from unittest.mock import patch

import pytest
from fastapi import HTTPException

from src.helpers import ratelimit


def _at(seconds: float):
    return patch.object(ratelimit.time, "time", return_value=seconds)


def test_wait_is_until_the_oldest_counted_hit_leaves_the_window():
    with _at(1000):
        assert ratelimit.rate_limit_wait("t", 2, "k", duration_minutes=10, consume_quota=True) == 0
    with _at(1100):
        assert ratelimit.rate_limit_wait("t", 2, "k", duration_minutes=10, consume_quota=True) == 0
    with _at(1200):
        # Window 600 s: the hit at 1000 frees a slot at 1600.
        assert ratelimit.rate_limit_wait("t", 2, "k", duration_minutes=10, consume_quota=True) == 400
    with _at(1600.5):
        assert ratelimit.rate_limit_wait("t", 2, "k", duration_minutes=10, consume_quota=True) == 0


def test_ensure_rate_limit_sends_retry_after():
    with _at(1000):
        ratelimit.ensure_rate_limit("t", 1, "k", duration_minutes=5)
    with _at(1060), pytest.raises(HTTPException) as exc:
        ratelimit.ensure_rate_limit("t", 1, "k", duration_minutes=5)
    assert exc.value.status_code == 429
    assert exc.value.headers == {"Retry-After": "240"}
