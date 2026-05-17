# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Pydantic schemas for organization invitations.

Lives next to `crud/organization_invitations.py`. Kept separate from
`schemas/organization.py` because invitations are a self-contained subdomain
with its own controller (`controllers/invitations.py`).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrganizationInvitationCreate(BaseModel):
    """Schema for creating an invitation."""

    email: EmailStr = Field(max_length=255)
    is_admin: bool = False


class OrganizationInvitationRead(BaseModel):
    """Schema for reading an invitation.

    `token` is included when the invitation belongs to the current user
    (`/invitations/pending`) so they can Accept/Decline directly. For owner-
    facing lists (per-org), `token` is omitted.
    """

    id: int
    organization_id: int
    organization_name: str | None = None
    email: str
    is_admin_invite: bool
    invited_by_user_id: int | None = None
    invited_by_name: str | None = None
    expires_at: datetime
    created_at: datetime
    token: str | None = None

    model_config = ConfigDict(from_attributes=True)


class OrganizationInvitationListResponse(BaseModel):
    """Response schema for a list of invitations."""

    items: list[OrganizationInvitationRead]


class PendingInvitationPreview(BaseModel):
    """Schema for the Accept/Decline preview page (accessible by token)."""

    organization_name: str
    is_admin_invite: bool
    invited_by_name: str | None = None
    email: str
    expires_at: datetime
