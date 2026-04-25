# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""User-related Pydantic schemas for API requests/responses."""

import datetime

from pydantic import BaseModel, Field, field_validator

from .organization import UserOrganizationInfo
from .user_ext import UserCustomData, UserPreviewCustomData


class UserRead(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    is_admin: bool
    is_premium: bool
    has_personal_subscription: bool = False
    custom_data: UserCustomData = Field(default_factory=UserCustomData)
    organizations: list[UserOrganizationInfo] = []

    class Config:
        from_attributes = True


class UserPreviewRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    custom_data: UserPreviewCustomData = Field(default_factory=UserPreviewCustomData)

    class Config:
        from_attributes = True

    # Replace last name with its first letter for privacy
    @field_validator("last_name")
    @classmethod
    def get_initials(cls, v: str) -> str:
        if v == "":
            return ""
        return v[0].upper() + "."


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
