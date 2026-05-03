# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Pydantic schemas for admin operations."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..helpers.user_display import display_for
from .event_log import EventLogRead
from .organization import UserOrganizationInfo
from .user import UserRead, UserToken
from .user_ext import UserCustomData


class AdminUserUpdate(BaseModel):
    """Schema for admin updating a user."""

    first_name: str | None = None
    last_name: str | None = None
    display_name: str | None = None
    email: str | None = None
    is_admin: bool | None = None
    is_premium: bool | None = None
    custom_data: UserCustomData | None = None


class AdminUserRead(BaseModel):
    """Extended user info for admin view."""

    id: int
    # Nullable: access-code users have no email/name; deleted users have
    # everything cleared. Admin UI uses display_label as the visible label.
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    display_name: str | None = None
    # Bool flags can be NULL in older rows (the columns are nullable in the
    # baseline schema). Coerce NULL → False at the API boundary so the admin
    # table doesn't trip on legacy data.
    is_admin: bool = False
    is_premium: bool = False
    email_confirmed: bool = False
    auth_method: str = "password"
    managed_account_group_id: int | None = None
    created_at: datetime | None
    deleted_at: datetime | None = None
    custom_data: UserCustomData = Field(default_factory=UserCustomData)
    organizations: list[UserOrganizationInfo] = []
    display_label: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("is_admin", "is_premium", "email_confirmed", mode="before")
    @classmethod
    def _none_to_false(cls, v: Any) -> Any:
        return False if v is None else v

    @model_validator(mode="after")
    def _populate_display_label(self) -> "AdminUserRead":
        self.display_label = display_for(self)
        return self


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
