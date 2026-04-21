# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Pydantic schemas for admin operations."""

from datetime import datetime

from pydantic import BaseModel, Field

from .event_log import EventLogRead
from .organization import UserOrganizationInfo
from .user import UserRead, UserToken
from .user_ext import UserCustomData


class AdminUserUpdate(BaseModel):
    """Schema for admin updating a user."""

    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    is_admin: bool | None = None
    is_premium: bool | None = None
    custom_data: UserCustomData | None = None


class AdminUserRead(BaseModel):
    """Extended user info for admin view."""

    id: int
    email: str
    first_name: str
    last_name: str
    is_admin: bool
    is_premium: bool
    email_confirmed: bool
    created_at: datetime | None
    deleted_at: datetime | None = None
    custom_data: UserCustomData = Field(default_factory=UserCustomData)
    organizations: list[UserOrganizationInfo] = []

    class Config:
        from_attributes = True


class AdminUserListResponse(BaseModel):
    """Paginated response for user list."""

    items: list[AdminUserRead]
    total: int
    limit: int
    offset: int


class AdminDashboardStats(BaseModel):
    """Dashboard statistics."""

    total_users: int
    admin_users: int
    premium_users: int
    recent_events: list[EventLogRead]


class ImpersonationRequest(BaseModel):
    """Request body for starting impersonation."""

    user_id: int


class ImpersonationResponse(BaseModel):
    """Response for impersonation endpoints."""

    access_token: str
    token_parsed: UserToken
    user: UserRead
    message: str
