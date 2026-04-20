# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Organization SQLAlchemy models (database table definitions)."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from ..helpers.db import Base


class OrganizationBase(Base):
    """SQLAlchemy model for organizations."""

    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)

    # Basic info
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    # Billing info
    phone = Column(String(50), nullable=True)
    tax_number = Column(String(100), nullable=True)
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(2), nullable=True)

    # Custom data (project-specific fields)
    custom_data = Column(JSONB, default=dict, nullable=False)

    # Stripe
    stripe_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_premium = Column(Boolean, default=False)
    stripe_quota = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True, default=None, index=True)

    # Relationships
    members = relationship(
        "UserOrganizationBase",
        back_populates="organization",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )


class UserOrganizationBase(Base):
    """SQLAlchemy model for user-organization memberships."""

    __tablename__ = "user_organizations"

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    is_admin = Column(Boolean, default=False)
    has_premium_seat = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("OrganizationBase", back_populates="members")
    user = relationship("UserBase", backref="organization_memberships")


class OrganizationInvitationBase(Base):
    """SQLAlchemy model for pending organization invitations."""

    __tablename__ = "organization_invitations"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email = Column(String(255), nullable=False, index=True)
    is_admin_invite = Column(Boolean, default=False, nullable=False)
    token = Column(String(64), nullable=False, unique=True, index=True)
    invited_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    declined_at = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("OrganizationBase")
    invited_by = relationship("UserBase", foreign_keys=[invited_by_user_id])
