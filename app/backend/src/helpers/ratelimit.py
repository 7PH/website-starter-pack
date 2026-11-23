# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Redis-backed rate limiting.

Counters live in Redis, shared across every uvicorn worker and instance, so a
per-IP cap is global. (The previous in-memory dict was per-worker, making the
effective cap N× the configured value once BACKEND_WORKERS > 1.)

Redis is mandatory infra. If it is unreachable the limiter FAILS EARLY — a short
socket timeout surfaces a 503 rather than silently allowing unthrottled traffic.

The algorithm is a sliding-window log (timestamps trimmed to the trailing
window), matching the old behavior, implemented as one atomic Lua script so a
crash between commands can never leave a counter without its TTL.
"""

import os
import time
import uuid

import redis
from fastapi import HTTPException, Request

from .logging import get_logger
from .real_ip import get_real_ip

logger = get_logger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

# Short timeouts so an unreachable Redis fails fast instead of hanging requests.
_redis = redis.Redis.from_url(
    REDIS_URL,
    socket_timeout=0.25,
    socket_connect_timeout=0.25,
    decode_responses=True,
)

# Sliding-window log over a sorted set, run atomically.
#   KEYS[1] = bucket key
#   ARGV[1] = now (seconds)   ARGV[2] = window seconds   ARGV[3] = quota
#   ARGV[4] = consume ("1"/"0")   ARGV[5] = unique member (used when consuming)
# Returns 0 when allowed, else the seconds until a slot frees up (at least 1).
_SLIDING_WINDOW_LUA = """
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', ARGV[1] - ARGV[2])
local count = redis.call('ZCARD', KEYS[1])
if count >= tonumber(ARGV[3]) then
  -- The hit whose expiry brings the count back under the quota.
  local oldest = redis.call('ZRANGE', KEYS[1], count - tonumber(ARGV[3]), count - tonumber(ARGV[3]), 'WITHSCORES')
  return math.max(1, math.ceil(tonumber(oldest[2]) + ARGV[2] - ARGV[1]))
end
if ARGV[4] == '1' then
  redis.call('ZADD', KEYS[1], ARGV[1], ARGV[5])
  redis.call('PEXPIRE', KEYS[1], math.ceil(ARGV[2] * 1000))
end
return 0
"""
_check_quota = _redis.register_script(_SLIDING_WINDOW_LUA)


def get_client_ip(request: Request) -> str:
    """Best-effort client IP for rate-limit keys, falling back to 'unknown'.

    Prefers `request.state.real_ip` (set by RealIPMiddleware) so rate limits
    bucket on the actual end user when behind a trusted reverse proxy.
    """
    return get_real_ip(request)


def rate_limit_wait(
    action: str,
    quota: float,
    key: str,
    duration_minutes: int = 1,
    consume_quota: bool = False,
) -> int:
    """Seconds until action/key is allowed again, 0 if it is now.

    When ``consume_quota`` is True and the quota is not yet reached, records the
    current hit. Raises HTTPException 503 if the Redis store is unreachable.
    """
    now = time.time()
    window_seconds = 60 * duration_minutes
    bucket = f"rl:{duration_minutes}:{action}:{key}"
    try:
        wait = _check_quota(
            keys=[bucket],
            args=[now, window_seconds, quota, "1" if consume_quota else "0", uuid.uuid4().hex],
        )
    except redis.RedisError as exc:
        logger.error("Rate-limit store unreachable (%s): %s", REDIS_URL, exc)
        raise HTTPException(status_code=503, detail="Service temporarily unavailable") from exc
    return int(wait)


def is_rate_limited(
    action: str,
    quota: float,
    key: str,
    duration_minutes: int = 1,
    consume_quota: bool = False,
) -> bool:
    """Return True if action/key has reached its quota in the trailing window."""
    return rate_limit_wait(action, quota, key, duration_minutes, consume_quota) > 0


def too_many_requests(wait_seconds: int) -> HTTPException:
    """429 telling the client how long to wait, so it can say "try again in 12 min" rather than "later"."""
    return HTTPException(
        status_code=429,
        detail="Too many requests. Please try again later.",
        headers={"Retry-After": str(max(1, wait_seconds))},
    )


def ensure_rate_limit(action: str, quota: float, key: str, duration_minutes: int = 1) -> None:
    """
    Ensure that the rate limit is not exceeded for a given action and key.
    If the rate limit is not reached, will consume 1 quota.
    If the rate limit is reached, will not consume quota but will raise an exception.

    :param action: The action to perform
    :param key: The key to use
    :param count: Maximum number of times the action can be performed per minute
    """
    if wait := rate_limit_wait(action, quota, key, duration_minutes, True):
        raise too_many_requests(wait)


def ensure_user_cooldown_and_daily(
    *,
    action: str,
    user_id: int,
    cooldown_minutes: int,
    daily_quota: float,
) -> None:
    """Pair a single-use cooldown with a daily cap, both keyed by ``user_id``.

    The daily bucket is namespaced as ``f"{action}-daily"`` so cooldown and daily
    counters never collide.
    """
    ensure_rate_limit(action=action, quota=1, key=str(user_id), duration_minutes=cooldown_minutes)
    ensure_rate_limit(
        action=f"{action}-daily",
        quota=daily_quota,
        key=str(user_id),
        duration_minutes=60 * 24,
    )
