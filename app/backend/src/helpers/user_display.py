# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Display-name resolution for users.

Single source of truth for "what label do we render for this user". Used by
both backend code and exposed to the frontend as `display_label` on UserRead /
UserPreviewRead / AdminUserRead.
"""

from ..constants import REAL_NAMES_ENABLED, USERNAMES_ENABLED


def display_for(user) -> str | None:
    """Return a human-friendly label, or None if the caller should i18n a fallback.

    Ladder:
        display_name → username → first and/or last name → email → None

    `display_name` stays on top: it's the deliberate override, so an app that
    sets both gets the one it set on purpose. The username rung applies only
    when USERNAMES_ENABLED, the name rung only when REAL_NAMES_ENABLED.

    Returns None for `auth_method='deleted'` so callers can render a localized
    "Deleted user" string instead of leaking the anonymized state.
    """
    if getattr(user, "auth_method", "password") == "deleted":
        return None

    name = getattr(user, "display_name", None)
    if name:
        return name

    # Flag-gated: an app that already had its own username column keeps the
    # labels it renders today until it opts in.
    if USERNAMES_ENABLED:
        username = getattr(user, "username", None)
        if username:
            return username

    # Google can send a first name without a last one: that still beats showing the email.
    if name := _real_name(user):
        return name

    return getattr(user, "email", None) or None


def _real_name(user) -> str:
    if not REAL_NAMES_ENABLED:
        return ""
    return " ".join(p for p in (getattr(user, "first_name", None), getattr(user, "last_name", None)) if p)


def billing_name(user) -> str:
    """Customer name for Stripe: the real name when collected, else the display label."""
    return _real_name(user) or display_for(user) or ""


def greeting_for(user) -> str | None:
    """Name to greet the user with in emails: their first name, else their display label."""
    if REAL_NAMES_ENABLED and getattr(user, "first_name", None):
        return user.first_name
    return display_for(user)
