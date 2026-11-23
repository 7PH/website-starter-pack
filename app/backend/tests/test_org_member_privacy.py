# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
"""Organization detail: plain members don't see each other's email."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.controllers import organizations as controller
from src.schemas.user import UserRead


def _membership(user_id: int, is_admin: bool) -> SimpleNamespace:
    user = SimpleNamespace(id=user_id, email=f"u{user_id}@example.com", first_name="F", last_name="L", is_premium=False)
    return SimpleNamespace(
        user=user, user_id=user_id, is_admin=is_admin, has_premium_seat=False, created_at=datetime.now(UTC)
    )


MEMBERS = [_membership(1, is_admin=True), _membership(2, is_admin=False), _membership(3, is_admin=False)]


def _viewer(user_id: int, site_admin: bool = False) -> UserRead:
    return UserRead(
        id=user_id,
        email=f"u{user_id}@example.com",
        first_name="F",
        last_name="L",
        is_admin=site_admin,
        is_premium=False,
    )


def _emails_seen_by(viewer: UserRead) -> dict[int, str | None]:
    membership = next((m for m in MEMBERS if m.user_id == viewer.id), None)
    org = SimpleNamespace(id=9)  # Only the id is read: building the full response is patched out.
    with (
        patch.object(controller, "get_organization_members", return_value=(MEMBERS, len(MEMBERS))),
        patch.object(controller, "get_user_org_membership", return_value=membership),
        patch.object(controller, "_build_org_read", side_effect=lambda org, total, premium, members: members),
    ):
        members = controller._org_to_read(MagicMock(), org, viewer)
    return {m.user_id: m.email for m in members}


def test_plain_member_sees_only_their_own_email():
    assert _emails_seen_by(_viewer(2)) == {1: None, 2: "u2@example.com", 3: None}


@pytest.mark.parametrize("viewer", [_viewer(1), _viewer(99, site_admin=True)], ids=["org admin", "site admin"])
def test_org_and_site_admins_see_every_email(viewer):
    assert all(_emails_seen_by(viewer).values())
