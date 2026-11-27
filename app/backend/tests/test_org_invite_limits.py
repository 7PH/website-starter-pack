# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Each invitation sends an email, so sending them needs a confirmed address and stays within limits."""

import os

os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")
os.environ.setdefault("TOKEN_HASH_SECRET", "test-secret-not-for-prod")

from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.controllers import organizations
from src.schemas.organization_invitation import OrganizationInvitationCreate
from src.schemas.user import UserRead


def _user(user_id: int = 1, confirmed: bool = True) -> UserRead:
    return UserRead(
        id=user_id, email=f"owner{user_id}@example.com", email_confirmed=confirmed, is_admin=False, is_premium=False
    )


@pytest.fixture
def org_state():
    """An org with no members or pending invitations; tests tweak the counts."""
    state = SimpleNamespace(members=1, pending=0, sent=MagicMock())
    with ExitStack() as stack:
        for name, value in {
            "ORG_INVITATIONS_ENABLED": True,
            "ORG_MAX_MEMBERS": 1000,
            "get_user_by_email": MagicMock(return_value=None),
            "count_organization_members": MagicMock(side_effect=lambda *_: state.members),
            "send_organization_invitation_email": state.sent,
            "log_event": MagicMock(),
            "_invitation_to_read": MagicMock(),
        }.items():
            stack.enter_context(patch.object(organizations, name, value))
        stack.enter_context(
            patch.object(
                organizations,
                "_check_org_access",
                side_effect=lambda _s, org_id, *_a, **_k: SimpleNamespace(id=org_id, name="Org", deleted_at=None),
            )
        )
        crud = organizations.invitations_crud
        stack.enter_context(patch.object(crud, "get_pending_invitation", return_value=None))
        stack.enter_context(patch.object(crud, "count_org_pending_invitations", side_effect=lambda *_: state.pending))
        stack.enter_context(
            patch.object(
                crud, "create_invitation", return_value=SimpleNamespace(token="t", email="x", is_admin_invite=False)
            )
        )
        stack.enter_context(patch.object(crud, "get_invitation_by_token", return_value=None))
        yield state


def _invite(user: UserRead, org_id: int = 1, n: int = 0):
    return organizations.create_invitation(
        session=MagicMock(),
        request=MagicMock(),
        user=user,
        org_id=org_id,
        invitation_data=OrganizationInvitationCreate(email=f"invitee{n}@example.com"),
    )


def test_unconfirmed_owner_cannot_invite(org_state):
    with pytest.raises(HTTPException) as exc:
        _invite(_user(confirmed=False))
    assert exc.value.status_code == 403
    org_state.sent.assert_not_called()


def test_pending_invitations_are_capped(org_state):
    org_state.pending = organizations.MAX_PENDING_INVITES_PER_ORG
    with pytest.raises(HTTPException) as exc:
        _invite(_user())
    assert exc.value.status_code == 400


def test_pending_invitations_count_toward_member_limit(org_state):
    org_state.members, org_state.pending = 3, 2
    with patch.object(organizations, "ORG_MAX_MEMBERS", 5), pytest.raises(HTTPException) as exc:
        _invite(_user())
    assert exc.value.status_code == 400


def test_one_user_sends_at_most_the_daily_quota(org_state):
    user = _user()
    # Spread over orgs so only the per-user limit applies.
    for n in range(organizations.INVITES_PER_USER_PER_DAY):
        _invite(user, org_id=100 + n, n=n)
    with pytest.raises(HTTPException) as exc:
        _invite(user, org_id=999)
    assert exc.value.status_code == 429


def test_one_org_receives_at_most_the_daily_quota(org_state):
    # Spread over owners so only the per-org limit applies.
    for n in range(organizations.INVITES_PER_ORG_PER_DAY):
        _invite(_user(user_id=100 + n), n=n)
    with pytest.raises(HTTPException) as exc:
        _invite(_user(user_id=999))
    assert exc.value.status_code == 429
