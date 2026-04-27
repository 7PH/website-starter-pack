# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Display-name resolution for users.

Single source of truth for "what label do we render for this user". Used by
both backend code and exposed to the frontend as `display_label` on UserRead /
UserPreviewRead / AdminUserRead.
"""


def display_for(user) -> str | None:
    """Return a human-friendly label, or None if the caller should i18n a fallback.

    Ladder:
        display_name → first_name + last_name → email → None

    Returns None for `auth_method='deleted'` so callers can render a localized
    "Deleted user" string instead of leaking the anonymized state.
    """
    if getattr(user, "auth_method", "password") == "deleted":
        return None

    name = getattr(user, "display_name", None)
    if name:
        return name

    first = getattr(user, "first_name", None)
    last = getattr(user, "last_name", None)
    if first and last:
        return f"{first} {last}"

    return getattr(user, "email", None) or None
