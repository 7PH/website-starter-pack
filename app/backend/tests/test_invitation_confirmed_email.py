# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Only a confirmed email address can see or answer the invitations sent to it."""

import os

os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")
os.environ.setdefault("TOKEN_HASH_SECRET", "test-secret-not-for-prod")

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.controllers import invitations
from src.schemas.user import UserRead

EMAIL = "invitee@example.com"


def _user(confirmed: bool) -> UserRead:
    return UserRead(id=5, email=EMAIL, email_confirmed=confirmed, is_admin=False, is_premium=False)


@pytest.fixture
def invitation():
    inv = SimpleNamespace(email=EMAIL, organization_id=3, is_admin_invite=True, accepted_at=None, declined_at=None)
    with (
        patch.object(invitations, "ORG_INVITATIONS_ENABLED", True),
        patch.object(invitations.invitations_crud, "get_invitation_by_token", return_value=inv),
        patch.object(invitations.invitations_crud, "is_expired", return_value=False),
        patch.object(invitations.invitations_crud, "mark_accepted"),
        patch.object(invitations.invitations_crud, "mark_declined") as declined,
        patch.object(invitations, "get_user_org_membership", return_value=None),
        patch.object(invitations, "count_user_organizations", return_value=0),
        patch.object(invitations, "count_organization_members", return_value=0),
        patch.object(invitations, "add_organization_member") as add,
        patch.object(invitations, "log_event"),
    ):
        yield SimpleNamespace(add=add, declined=declined)


def test_pending_list_is_empty_until_email_is_confirmed():
    with (
        patch.object(invitations, "ORG_INVITATIONS_ENABLED", True),
        patch.object(invitations.invitations_crud, "list_user_pending_invitations") as listed,
    ):
        result = invitations.list_my_pending_invitations(session=MagicMock(), user=_user(confirmed=False))
    assert result.items == []
    listed.assert_not_called()


@pytest.mark.parametrize("answer", [invitations.accept_invitation, invitations.decline_invitation])
def test_unconfirmed_email_cannot_answer(invitation, answer):
    with pytest.raises(HTTPException) as exc:
        answer(session=MagicMock(), request=MagicMock(), user=_user(confirmed=False), token="t")
    assert exc.value.status_code == 403
    invitation.add.assert_not_called()
    invitation.declined.assert_not_called()


def test_confirmed_email_accepts(invitation):
    invitations.accept_invitation(session=MagicMock(), request=MagicMock(), user=_user(confirmed=True), token="t")
    invitation.add.assert_called_once()
