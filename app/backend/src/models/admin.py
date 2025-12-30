# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Pydantic models for admin operations.
"""

from datetime import datetime

from pydantic import BaseModel

from .event_log import EventLogRead
from .user import UserRead, UserToken


class AdminUserUpdate(BaseModel):
    """Schema for admin updating a user."""

    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    is_admin: bool | None = None
    is_premium: bool | None = None


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
    last_seen_at: datetime | None

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


class ImpersonationResponse(BaseModel):
    """Response for impersonation endpoints."""

    access_token: str
    token_parsed: UserToken
    user: UserRead
    message: str
