# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""User SQLAlchemy model (database table definition)."""

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB

from ..helpers.db import Base


class UserBase(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # Nullable: access-code users have no email (kids/kiosks/shared devices).
    # Postgres allows multiple NULLs under a UNIQUE constraint natively.
    email = Column(String, unique=True, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email_confirmed = Column(Boolean, default=False)
    # Nullable: OAuth users may have no password; access-code users never do.
    hashed_password = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    stripe_id = Column(String, nullable=True)
    is_premium = Column(Boolean, default=False)
    has_personal_subscription = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True, default=None)
    oauth_provider = Column(String, nullable=True)  # OAuthProvider value
    oauth_id = Column(String, nullable=True)  # Provider's unique user ID

    # 'password' | 'oauth' | 'access_code' | 'deleted' — enforced by the CHECK below.
    auth_method = Column(String(32), nullable=False, default="password", server_default="password")

    # Set for managed accounts (users with auth_method='access_code'). Points
    # to the group they belong to; the group's owner_id is the responsible user.
    # Apps that don't use this concept leave it NULL.
    managed_account_group_id = Column(
        Integer,
        ForeignKey("managed_account_groups.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Preferred label. First in the display ladder (above first_name+last_name).
    # Use it for users where the first/last split doesn't fit (kids using a
    # nickname, kiosk users, service accounts).
    display_name = Column(String(255), nullable=True)

    # Custom data (project-specific fields; validated against UserCustomData)
    custom_data = Column(JSONB, default=dict, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "(auth_method = 'password'    AND email IS NOT NULL AND hashed_password IS NOT NULL AND oauth_provider IS NULL)"
            " OR (auth_method = 'oauth'    AND email IS NOT NULL AND oauth_provider IS NOT NULL)"
            " OR (auth_method = 'access_code')"
            " OR (auth_method = 'deleted')",
            name="users_auth_integrity",
        ),
    )

    # This table is used for polymorphic inheritance
    __mapper_args__ = {"polymorphic_identity": "userbase"}
