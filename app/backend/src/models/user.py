# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import datetime

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from ..helpers.db import Base


class UserBase(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email_confirmed = Column(Boolean, default=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    stripe_id = Column(String, nullable=True)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True, default=None)

    # This table is used for polymorphic inheritance
    __mapper_args__ = {"polymorphic_identity": "userbase"}


class UserRead(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    is_admin: bool
    is_premium: bool

    class Config:
        from_attributes = True


class UserPreviewRead(BaseModel):
    id: int
    first_name: str
    last_name: str

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

    @field_validator("last_name")
    @classmethod
    def to_uppercase(cls, v: str) -> str:
        return v.upper()


class UserChangeInfo(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=255)


class UserChangePassword(BaseModel):
    old_password: str = Field(max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


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
