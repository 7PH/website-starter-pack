# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Users without names or an email (seeded, pseudonymous, managed) must not break member or conversation listings."""

from datetime import UTC, datetime
from types import SimpleNamespace

from src.controllers.conversations import _user_preview
from src.controllers.organizations import _membership_to_read


def _nameless_user():
    return SimpleNamespace(
        id=9,
        email=None,
        first_name=None,
        last_name=None,
        display_name=None,
        username=None,
        auth_method="access_code",
        is_premium=False,
    )


def test_member_without_names_is_listed():
    membership = SimpleNamespace(is_admin=False, has_premium_seat=False, created_at=datetime.now(UTC))
    read = _membership_to_read(membership, _nameless_user())
    assert read.first_name is None
    assert read.last_name is None


def test_conversation_preview_without_names_or_email():
    preview = _user_preview(_nameless_user())
    assert (preview.email, preview.first_name, preview.last_name) == (None, None, None)
