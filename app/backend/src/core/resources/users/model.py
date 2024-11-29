import datetime

from pydantic import BaseModel, field_validator
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from src.db import Base


class UserBase(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email_confirmed = Column(Boolean, default=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    newsletter_on = Column(Boolean, default=True)
    password_reset_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    last_seen_at = Column(DateTime, default=datetime.datetime.now)

    # This table is used for polymorphic inheritance
    __mapper_args__ = {"polymorphic_identity": "userbase"}


class UserRead(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    is_admin: bool

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
    email: str
    password: str
    first_name: str
    last_name: str

    @field_validator("last_name")
    @classmethod
    def to_uppercase(cls, v: str) -> str:
        return v.upper()


class UserLogin(BaseModel):
    email: str
    password: str


class UserChangeInfo(BaseModel):
    first_name: str
    last_name: str
    email: str


class UserChangePassword(BaseModel):
    old_password: str
    new_password: str


class UserToken(BaseModel):
    user: UserRead
    created_at: datetime.datetime
    expires_at: datetime.datetime


class UserTokenUpdate(BaseModel):
    access_token: str
    token_parsed: UserToken
    user: UserRead
    token_type: str = "bearer"


class UserPasswordResetRequest(BaseModel):
    email: str


class UserPasswordResetConfirm(BaseModel):
    email: str
    password: str
    token: str
