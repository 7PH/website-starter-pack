# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Conversation-related Pydantic schemas for API requests/responses."""

from datetime import datetime

from pydantic import BaseModel, Field

from ..constants_ext import UserInitiableSubtype

# Field length constants (shared across schemas)
SUBJECT_MAX_LENGTH = 255
MESSAGE_MAX_LENGTH = 10000


class ConversationUserPreview(BaseModel):
    """User preview for conversation context, includes email for admin visibility."""

    id: int
    email: str
    first_name: str
    last_name: str


class MessageCreate(BaseModel):
    """Schema for creating a new message."""

    content: str = Field(min_length=1, max_length=MESSAGE_MAX_LENGTH)


class MessageRead(BaseModel):
    """Schema for reading a message."""

    id: int
    conversation_id: int
    sender_id: int | None
    sender: ConversationUserPreview | None = None
    content: str
    is_admin_response: bool = False
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    """Schema for creating a new support conversation."""

    subject: str = Field(min_length=1, max_length=SUBJECT_MAX_LENGTH)
    content: str = Field(min_length=1, max_length=MESSAGE_MAX_LENGTH)
    subtype: UserInitiableSubtype | None = None


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation (admin only)."""

    is_closed: bool | None = None


class ConversationRead(BaseModel):
    """Schema for reading a conversation."""

    id: int
    type: str
    subtype: str | None = None
    subject: str | None = None
    created_by_id: int | None = None
    created_by: ConversationUserPreview | None = None
    is_closed: bool = False
    closed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    unread_count: int = 0  # Computed field
    last_message: MessageRead | None = None  # Preview of last message

    class Config:
        from_attributes = True


class ConversationDetail(ConversationRead):
    """Schema for conversation with messages."""

    messages: list[MessageRead] = []


class ConversationListResponse(BaseModel):
    """Paginated response for conversation list."""

    items: list[ConversationRead]
    total: int
    limit: int
    offset: int


class MessageListResponse(BaseModel):
    """Paginated response for messages in a conversation."""

    items: list[MessageRead]
    total: int
    limit: int
    offset: int
    has_more: bool


class AdminConversationCreate(BaseModel):
    """Schema for admin creating a conversation with specific users."""

    subject: str = Field(min_length=1, max_length=SUBJECT_MAX_LENGTH)
    content: str = Field(min_length=1, max_length=MESSAGE_MAX_LENGTH)
    subtype: UserInitiableSubtype | None = None
    participant_user_ids: list[int] = Field(min_length=1)
