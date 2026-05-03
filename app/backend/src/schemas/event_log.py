# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Event log Pydantic schemas for API requests/responses."""

import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class EventLogCreate(BaseModel):
    """Input schema for creating an event log."""

    action: str
    details: dict[str, Any] | None = None


class EventLogRead(BaseModel):
    """Output schema for reading event logs."""

    id: int
    user_id: int | None
    action: str
    details: dict[str, Any] | None = None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime.datetime | None

    model_config = ConfigDict(from_attributes=True)


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
