import time

from fastapi import HTTPException

entries = {
    # duration min -> action -> key -> [timestamps]
}


def cleanup_entries():
    """
    Cleanup function. Called every minute.
    """
    for duration_minutes in entries:
        for action in entries[duration_minutes]:
            for key in entries[duration_minutes][action]:
                # If latest entry is older than 1 minute, remove all
                if (
                    len(entries[duration_minutes][action][key]) == 0
                    or entries[duration_minutes][action][key][-1] < time.time() - 60
                ):
                    del entries[duration_minutes][action][key]


def is_rate_limited(
    action: str,
    quota: float,
    key: str,
    duration_minutes: int = 1,
    consume_quota: bool = False,
) -> bool:
    """
    Rate limit function. Returns False is exceeding quota.
    """
    # Ensure that entries[duration_minutes][action][key] exists
    if duration_minutes not in entries:
        entries[duration_minutes] = {}
    if action not in entries[duration_minutes]:
        entries[duration_minutes][action] = {}
    if key not in entries[duration_minutes][action]:
        entries[duration_minutes][action][key] = []

    # Remove obsolete entries
    # actions[action][key] = [x for x in actions[action][key] if x > time.time() - 60 * duration_minutes] # Not done for performance reasons -> see below
    while (
        len(entries[duration_minutes][action][key]) > 0
        and entries[duration_minutes][action][key][0]
        < time.time() - 60 * duration_minutes
    ):
        entries[duration_minutes][action][key].pop(0)

    # Quota exceeded
    if len(entries[duration_minutes][action][key]) >= quota:
        return True

    # Add current entry
    if consume_quota:
        entries[duration_minutes][action][key].append(time.time())
    return False


def ensure_rate_limit(
    action: str, quota: float, key: str, duration_minutes: int = 1
) -> None:
    """
    Ensure that the rate limit is not exceeded for a given action and key.
    If the rate limit is not reached, will consume 1 quota.
    If the rate limit is reached, will not consume quota but will raise an exception.

    :param action: The action to perform
    :param key: The key to use
    :param count: Maximum number of times the action can be performed per minute
    """
    if is_rate_limited(action, quota, key, duration_minutes, True):
        raise HTTPException(status_code=429, detail="Merci de patienter un peu.")
