# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Invitation-side endpoints (preview + Accept/Decline by token)."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..constants import ORG_INVITATIONS_ENABLED, ORG_MAX_MEMBERS, ORG_MAX_PER_USER, EventType
from ..crud import organization_invitations as invitations_crud
from ..crud.event_logs import log_event
from ..crud.organizations import (
    add_organization_member,
    count_organization_members,
    count_user_organizations,
    get_user_org_membership,
)
from ..helpers.auth import get_current_nonmanaged_user, get_current_user
from ..helpers.db import get_session
from ..schemas.organization import (
    OrganizationInvitationListResponse,
    OrganizationInvitationRead,
    PendingInvitationPreview,
)
from ..schemas.user import UserRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/invitations")


def _invitation_to_read(invitation, include_token: bool = False) -> OrganizationInvitationRead:
    inviter = invitation.invited_by
    inviter_name = None
    if inviter:
        inviter_name = f"{inviter.first_name} {inviter.last_name}".strip() or inviter.email
    return OrganizationInvitationRead(
        id=invitation.id,
        organization_id=invitation.organization_id,
        organization_name=invitation.organization.name if invitation.organization else None,
        email=invitation.email,
        is_admin_invite=invitation.is_admin_invite,
        invited_by_user_id=invitation.invited_by_user_id,
        invited_by_name=inviter_name,
        expires_at=invitation.expires_at,
        created_at=invitation.created_at,
        token=invitation.token if include_token else None,
    )


def _enabled_or_404():
    if not ORG_INVITATIONS_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitations are disabled")


@router.get("/pending", response_model=OrganizationInvitationListResponse)
def list_my_pending_invitations(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_current_user),
):
    """List pending invitations matching the current user's email."""
    if not ORG_INVITATIONS_ENABLED:
        return OrganizationInvitationListResponse(items=[])
    pending = invitations_crud.list_user_pending_invitations(session, user.email)
    return OrganizationInvitationListResponse(
        items=[_invitation_to_read(inv, include_token=True) for inv in pending]
    )


@router.get("/{token}", response_model=PendingInvitationPreview)
def preview_invitation(*, session: Session = Depends(get_session), token: str):
    """Public preview of an invitation (used before login/signup)."""
    _enabled_or_404()
    invitation = invitations_crud.get_invitation_by_token(session, token)
    if not invitation or invitation.accepted_at or invitation.declined_at:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
    if invitations_crud.is_expired(invitation):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invitation expired")

    inviter_name = None
    if invitation.invited_by:
        inviter_name = (
            f"{invitation.invited_by.first_name} {invitation.invited_by.last_name}".strip()
            or invitation.invited_by.email
        )
    return PendingInvitationPreview(
        organization_name=invitation.organization.name if invitation.organization else "",
        is_admin_invite=invitation.is_admin_invite,
        invited_by_name=inviter_name,
        email=invitation.email,
        expires_at=invitation.expires_at,
    )


@router.post("/{token}/accept", status_code=status.HTTP_204_NO_CONTENT)
def accept_invitation(
    *,
    session: Session = Depends(get_session),
    request: Request,
    user: UserRead = Depends(get_current_nonmanaged_user),
    token: str,
):
    """Accept an invitation. Current user's email must match."""
    _enabled_or_404()
    invitation = invitations_crud.get_invitation_by_token(session, token)
    if not invitation or invitation.accepted_at or invitation.declined_at:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
    if invitations_crud.is_expired(invitation):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invitation expired")
    if invitation.email.lower() != user.email.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invitation is for a different email")

    # Already a member?
    if get_user_org_membership(session, user.id, invitation.organization_id):
        invitations_crud.mark_accepted(session, invitation)
        return

    if count_user_organizations(session, user.id) >= ORG_MAX_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum of {ORG_MAX_PER_USER} organization(s) reached",
        )
    if count_organization_members(session, invitation.organization_id) >= ORG_MAX_MEMBERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization has reached the maximum of {ORG_MAX_MEMBERS} member(s)",
        )

    add_organization_member(
        session,
        user.id,
        invitation.organization_id,
        is_admin=invitation.is_admin_invite,
    )
    invitations_crud.mark_accepted(session, invitation)

    log_event(
        session,
        action=EventType.ORG_INVITATION_ACCEPTED,
        user_id=user.id,
        details={"org_id": invitation.organization_id, "is_admin": invitation.is_admin_invite},
        request=request,
    )


@router.post("/{token}/decline", status_code=status.HTTP_204_NO_CONTENT)
def decline_invitation(
    *,
    session: Session = Depends(get_session),
    request: Request,
    user: UserRead = Depends(get_current_nonmanaged_user),
    token: str,
):
    """Decline an invitation. Current user's email must match."""
    _enabled_or_404()
    invitation = invitations_crud.get_invitation_by_token(session, token)
    if not invitation or invitation.accepted_at or invitation.declined_at:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
    if invitation.email.lower() != user.email.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invitation is for a different email")

    invitations_crud.mark_declined(session, invitation)

    log_event(
        session,
        action=EventType.ORG_INVITATION_DECLINED,
        user_id=user.id,
        details={"org_id": invitation.organization_id},
        request=request,
    )
