# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""User-related Pydantic schemas for API requests/responses."""

import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from ..helpers.user_display import display_for
from .organization import UserOrganizationInfo
from .user_ext import UserCustomData, UserPreviewCustomData


class UserRead(BaseModel):
    id: int
    # Nullable on read schemas: access-code users have no email/name; deleted
    # users have everything cleared. Frontends fall back to display_label.
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    display_name: str | None = None
    is_admin: bool
    is_premium: bool
    has_personal_subscription: bool = False
    auth_method: str = "password"
    # Set for managed accounts (auth_method='access_code'); None otherwise.
    managed_account_group_id: int | None = None
    custom_data: UserCustomData = Field(default_factory=UserCustomData)
    organizations: list[UserOrganizationInfo] = []
    # Computed below; one source of truth for "what label do we show?".
    display_label: str | None = None

    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def _populate_display_label(self) -> "UserRead":
        self.display_label = display_for(self)
        return self


class UserPreviewRead(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    display_name: str | None = None
    auth_method: str = "password"
    custom_data: UserPreviewCustomData = Field(default_factory=UserPreviewCustomData)
    display_label: str | None = None

    class Config:
        from_attributes = True

    # Replace last name with its first letter for privacy
    @field_validator("last_name")
    @classmethod
    def get_initials(cls, v: str | None) -> str | None:
        if not v:
            return v
        return v[0].upper() + "."

    @model_validator(mode="after")
    def _populate_display_label(self) -> "UserPreviewRead":
        self.display_label = display_for(self)
        return self


class UserCreate(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    custom_data: UserCustomData | None = None

    @field_validator("last_name")
    @classmethod
    def to_uppercase(cls, v: str) -> str:
        return v.upper()


class UserChangeInfo(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    custom_data: UserCustomData | None = None


class UserChangePassword(BaseModel):
    old_password: str = Field(max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class UserChangeEmail(BaseModel):
    new_email: str = Field(max_length=255)
    password: str = Field(max_length=128)


class EmailChangeConfirm(BaseModel):
    """Confirm email change with JWT token."""

    token: str


class UserToken(BaseModel):
    user: UserRead
    created_at: datetime.datetime
    expires_at: datetime.datetime
    real_admin_id: int | None = None


class UserTokenUpdate(BaseModel):
    access_token: str
    token_parsed: UserToken
    user: UserRead
    token_type: str = "bearer"


class UserPasswordResetRequest(BaseModel):
    email: str


class EmailVerificationConfirm(BaseModel):
    """Confirm email verification with JWT token."""

    token: str


class PasswordResetConfirmJWT(BaseModel):
    """Confirm password reset using JWT token (no email needed)."""

    token: str
    password: str


class AuthMessageResponse(BaseModel):
    """Standard response for auth operations."""

    message: str


class AccountDeletionInfo(BaseModel):
    """Info returned to render the account-deletion confirmation page."""

    requires_password: bool
    email_masked: str


class AccountDeletionConfirm(BaseModel):
    """Confirm account deletion with JWT token and optional password."""

    token: str
    password: str | None = None


class SignInWithCodeRequest(BaseModel):
    """POST /auth/code body. Both fields live in the body (not the URL) so
    they stay out of access logs, browser history, and Referer headers.

    `managed_account_id` scopes the code lookup so an attacker who guesses a
    code still has to know which account it belongs to.
    """

    managed_account_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=128)
