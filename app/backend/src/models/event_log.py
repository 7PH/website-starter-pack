# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Event logging models for tracking user and admin actions.
"""

import datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from ..helpers.db import Base


class EventLogBase(Base):
    """SQLAlchemy model for event logs."""

    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    details = Column(JSONB, default=dict)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now, index=True)

    # Composite index for user event history queries
    __table_args__ = (
        Index("idx_event_logs_user_created", "user_id", created_at.desc()),
    )


class EventLogCreate(BaseModel):
    """Input schema for creating an event log."""

    action: str
    details: dict[str, Any] | None = None


class EventLogRead(BaseModel):
    """Output schema for reading event logs."""

    id: int
    user_id: int | None
    action: str
    details: dict[str, Any]
    ip_address: str | None
    user_agent: str | None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class EventLogFilter(BaseModel):
    """Query parameters for filtering event logs."""

    user_id: int | None = None
    action: str | None = None
    action_prefix: str | None = None  # e.g., "user." to get all user events
    from_date: datetime.datetime | None = None
    to_date: datetime.datetime | None = None


class EventLogListResponse(BaseModel):
    """Paginated response for event logs."""

    items: list[EventLogRead]
    total: int
    limit: int
    offset: int
