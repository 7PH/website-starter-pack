# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
CRUD operations for event logs.
"""

from typing import Any

from fastapi import Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.event_log import EventLogBase, EventLogFilter, EventLogRead


def log_event(
    session: Session,
    action: str,
    user_id: int | None = None,
    details: dict[str, Any] | None = None,
    request: Request | None = None,
) -> EventLogBase:
    """
    Log an event to the database.

    Args:
        session: Database session
        action: Event action type (e.g., "user.login", "admin.impersonate")
        user_id: ID of the user the event is about (optional)
        details: Additional event details as JSON (optional)
        request: FastAPI request object to extract IP and user agent (optional)

    Returns:
        The created event log entry
    """
    ip_address = None
    user_agent = None

    if request:
        # Get client IP (handle proxies)
        forwarded = request.headers.get("X-Forwarded-For")
        ip_address = forwarded.split(",")[0].strip() if forwarded else request.client.host if request.client else None

        user_agent = request.headers.get("User-Agent")

    event = EventLogBase(
        user_id=user_id,
        action=action,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def get_events(
    session: Session,
    filters: EventLogFilter | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[EventLogRead], int]:
    """
    Get event logs with optional filtering.

    Args:
        session: Database session
        filters: Optional filters to apply
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        Tuple of (list of events, total count)
    """
    query = session.query(EventLogBase)

    if filters:
        if filters.user_id is not None:
            query = query.filter(EventLogBase.user_id == filters.user_id)
        if filters.action is not None:
            query = query.filter(EventLogBase.action == filters.action)
        if filters.action_prefix is not None:
            query = query.filter(EventLogBase.action.startswith(filters.action_prefix))
        if filters.from_date is not None:
            query = query.filter(EventLogBase.created_at >= filters.from_date)
        if filters.to_date is not None:
            query = query.filter(EventLogBase.created_at <= filters.to_date)

    # Get total count before pagination
    total = query.count()

    # Apply ordering and pagination
    events = query.order_by(EventLogBase.created_at.desc()).offset(offset).limit(limit).all()

    return [EventLogRead.model_validate(e) for e in events], total


def get_user_events(
    session: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[EventLogRead], int]:
    """
    Get events for a specific user.

    Args:
        session: Database session
        user_id: User ID to filter by
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        Tuple of (list of events, total count)
    """
    query = session.query(EventLogBase).filter(EventLogBase.user_id == user_id)

    total = query.count()
    events = query.order_by(EventLogBase.created_at.desc()).offset(offset).limit(limit).all()

    return [EventLogRead.model_validate(e) for e in events], total


def get_recent_events(
    session: Session,
    limit: int = 10,
) -> list[EventLogRead]:
    """
    Get the most recent events (for dashboard).

    Args:
        session: Database session
        limit: Maximum number of results

    Returns:
        List of recent events
    """
    events = session.query(EventLogBase).order_by(EventLogBase.created_at.desc()).limit(limit).all()
    return [EventLogRead.model_validate(e) for e in events]


def get_event_stats(session: Session) -> dict[str, int]:
    """
    Get event statistics for dashboard.

    Returns:
        Dictionary with event counts by action prefix
    """
    # Count events by category (action prefix)
    results = (
        session.query(
            func.split_part(EventLogBase.action, ".", 1).label("category"),
            func.count().label("count"),
        )
        .group_by("category")
        .all()
    )
    return {r.category: r.count for r in results}
