# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""CRUD operations for organization invitations."""

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..models.organization import OrganizationInvitationBase


def _now() -> datetime:
    return datetime.now(UTC)


def create_invitation(
    session: Session,
    *,
    organization_id: int,
    email: str,
    is_admin_invite: bool,
    invited_by_user_id: int | None,
    expiry_days: int,
) -> OrganizationInvitationBase:
    """Create a new invitation with a secure random token."""
    invitation = OrganizationInvitationBase(
        organization_id=organization_id,
        email=email.lower(),
        is_admin_invite=is_admin_invite,
        token=secrets.token_urlsafe(32),
        invited_by_user_id=invited_by_user_id,
        expires_at=_now() + timedelta(days=expiry_days),
    )
    session.add(invitation)
    session.commit()
    session.refresh(invitation)
    return invitation


def get_invitation_by_token(session: Session, token: str) -> OrganizationInvitationBase | None:
    """Load an invitation by its token, with org and inviter relationships loaded."""
    return session.execute(
        select(OrganizationInvitationBase)
        .where(OrganizationInvitationBase.token == token)
        .options(
            joinedload(OrganizationInvitationBase.organization),
            joinedload(OrganizationInvitationBase.invited_by),
        )
    ).scalar_one_or_none()


def get_invitation_by_id(session: Session, invitation_id: int) -> OrganizationInvitationBase | None:
    return session.get(OrganizationInvitationBase, invitation_id)


def _pending_filters() -> list:
    return [
        OrganizationInvitationBase.accepted_at.is_(None),
        OrganizationInvitationBase.declined_at.is_(None),
        OrganizationInvitationBase.expires_at > _now(),
    ]


def get_pending_invitation(
    session: Session, organization_id: int, email: str
) -> OrganizationInvitationBase | None:
    return session.execute(
        select(OrganizationInvitationBase).where(
            OrganizationInvitationBase.organization_id == organization_id,
            OrganizationInvitationBase.email == email.lower(),
            *_pending_filters(),
        )
    ).scalar_one_or_none()


def list_org_pending_invitations(
    session: Session, organization_id: int
) -> list[OrganizationInvitationBase]:
    return list(
        session.execute(
            select(OrganizationInvitationBase)
            .options(
                # _invitation_to_read reads both relations; eager-load to avoid
                # N+1 when rendering a long invitation list.
                joinedload(OrganizationInvitationBase.invited_by),
                joinedload(OrganizationInvitationBase.organization),
            )
            .where(
                OrganizationInvitationBase.organization_id == organization_id,
                *_pending_filters(),
            )
            .order_by(OrganizationInvitationBase.created_at.desc())
        )
        .scalars()
        .all()
    )


def list_user_pending_invitations(
    session: Session, email: str
) -> list[OrganizationInvitationBase]:
    return list(
        session.execute(
            select(OrganizationInvitationBase)
            .where(
                OrganizationInvitationBase.email == email.lower(),
                *_pending_filters(),
            )
            .options(joinedload(OrganizationInvitationBase.organization))
            .order_by(OrganizationInvitationBase.created_at.desc())
        )
        .scalars()
        .all()
    )


def mark_accepted(session: Session, invitation: OrganizationInvitationBase) -> None:
    invitation.accepted_at = _now()
    session.commit()


def mark_declined(session: Session, invitation: OrganizationInvitationBase) -> None:
    invitation.declined_at = _now()
    session.commit()


def delete_invitation(session: Session, invitation: OrganizationInvitationBase) -> None:
    session.delete(invitation)
    session.commit()


def is_expired(invitation: OrganizationInvitationBase) -> bool:
    return invitation.expires_at <= _now()
