import datetime

from pydantic import BaseModel, validator
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email_confirmed = Column(Boolean, default=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    newsletter_on = Column(Boolean, default=True)
    password_reset_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    last_seen_at = Column(DateTime, default=datetime.datetime.now)


class UserRead(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    is_admin: bool


class UserPreviewRead(BaseModel):
    id: int
    first_name: str
    last_name: str

    # Replace last name with its first letter for privacy
    @validator("last_name")
    def get_initials(cls, v):
        if v == "":
            return ""
        return v[0].upper() + "."


class UserCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str

    @validator("last_name")
    def to_uppercase(cls, v):
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
    token_raw: str
    token_parsed: UserToken
    user: UserRead


class UserPasswordResetRequest(BaseModel):
    email: str


class UserPasswordResetConfirm(BaseModel):
    email: str
    password: str
    token: str
