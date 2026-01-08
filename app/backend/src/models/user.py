# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""User SQLAlchemy model (database table definition)."""

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
