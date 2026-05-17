# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Conversation and Message SQLAlchemy models (database table definitions)."""

import enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.orm import relationship

from ..helpers.db import Base


class ConversationType(enum.StrEnum):
    """Type of conversation."""

    SUPPORT = "support"
    DIRECT = "direct"  # Future use


class ConversationBase(Base):
    """SQLAlchemy model for conversations."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)

    # Conversation metadata
    type = Column(String(50), nullable=False, default=ConversationType.SUPPORT.value, index=True)
    subject = Column(String(255), nullable=True)
    subtype = Column(String(100), nullable=True, index=True)

    # For support: the user who initiated the conversation
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Status tracking
    is_closed = Column(Boolean, default=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    created_by = relationship("UserBase", foreign_keys=[created_by_id])
    messages = relationship(
        "MessageBase",
        back_populates="conversation",
        lazy="dynamic",
        order_by="MessageBase.created_at",
    )
    participants = relationship(
        "ConversationParticipantBase",
        back_populates="conversation",
        lazy="dynamic",
    )


class MessageBase(Base):
    """SQLAlchemy model for messages within a conversation."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Message content
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    content = Column(Text, nullable=False)

    # For support messages: distinguish user vs admin responses
    is_admin_response = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    conversation = relationship("ConversationBase", back_populates="messages")
    sender = relationship("UserBase")

    __table_args__ = (
        # Composite index for "newest message per conversation" lookups
        # (get_last_message, get_messages with ORDER BY created_at DESC).
        # DESC matches the migration so model-built and migration-built DBs agree.
        Index("idx_messages_conv_created", "conversation_id", text("created_at DESC")),
    )


class ConversationParticipantBase(Base):
    """SQLAlchemy model for conversation participants (for direct messages and read tracking)."""

    __tablename__ = "conversation_participants"

    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    # Read tracking
    last_read_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    conversation = relationship("ConversationBase", back_populates="participants")
    user = relationship("UserBase")
