# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Managed account group SQLAlchemy model.

A ManagedAccountGroup is a named container of managed accounts (users with
auth_method='access_code' that have no email/password of their own and sign in
by code). One owner (a regular user) can create many groups; each group has a
public share_token that lets a managed account find their name in a list.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from ..helpers.db import Base


class ManagedAccountGroupBase(Base):
    __tablename__ = "managed_account_groups"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    share_token = Column(String(32), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=True)
