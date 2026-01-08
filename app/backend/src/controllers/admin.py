# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Admin controller for user management, impersonation, and event logs.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..constants import EventType
from ..crud.event_logs import get_events, get_user_events, log_event
from ..crud.users import get_user_by_id, soft_delete_user, update_user
from ..helpers.auth import create_access_token, get_current_admin, get_real_admin_id
from ..helpers.db import get_session
from ..models.user import UserBase
from ..schemas.admin import (
    AdminDashboardStats,
    AdminUserListResponse,
    AdminUserRead,
    AdminUserUpdate,
    ImpersonationResponse,
)
from ..schemas.event_log import EventLogFilter, EventLogListResponse
from ..schemas.user import UserRead

router = APIRouter(prefix="/admin")


# ============================================================================
# Dashboard
# ============================================================================


@router.get("/dashboard", response_model=AdminDashboardStats)
def get_dashboard_stats(
    *,
    session: Session = Depends(get_session),
    admin: UserRead = Depends(get_current_admin),
):
    """Get dashboard statistics (excludes deleted users)."""
    total_users = session.query(func.count(UserBase.id)).filter(UserBase.deleted_at.is_(None)).scalar()
    admin_users = (
        session.query(func.count(UserBase.id)).filter(UserBase.is_admin, UserBase.deleted_at.is_(None)).scalar()
    )
    premium_users = (
        session.query(func.count(UserBase.id)).filter(UserBase.is_premium, UserBase.deleted_at.is_(None)).scalar()
    )

    # Get recent events
    recent_events, _ = get_events(session, limit=10)

    return AdminDashboardStats(
        total_users=total_users,
        admin_users=admin_users,
        premium_users=premium_users,
        recent_events=recent_events,
    )


# ============================================================================
# User management
# ============================================================================


@router.get("/users", response_model=AdminUserListResponse)
def list_users(
    *,
    session: Session = Depends(get_session),
    admin: UserRead = Depends(get_current_admin),
    search: str | None = Query(None, max_length=100),
    is_admin: bool | None = None,
    is_premium: bool | None = None,
    include_deleted: bool = False,
    only_deleted: bool = False,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List all users with optional search and filters."""
    query = session.query(UserBase)

    # Handle deleted user filtering
    if only_deleted:
        query = query.filter(UserBase.deleted_at.isnot(None))
    elif not include_deleted:
        query = query.filter(UserBase.deleted_at.is_(None))

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (UserBase.email.ilike(search_pattern))
            | (UserBase.first_name.ilike(search_pattern))
            | (UserBase.last_name.ilike(search_pattern))
        )

    if is_admin is not None:
        query = query.filter(UserBase.is_admin == is_admin)

    if is_premium is not None:
        query = query.filter(UserBase.is_premium == is_premium)

    total = query.count()
    users = query.order_by(UserBase.created_at.desc()).offset(offset).limit(limit).all()

    return AdminUserListResponse(
        items=[AdminUserRead.model_validate(u) for u in users],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/users/{user_id}", response_model=AdminUserRead)
def get_user_detail(
    *,
    session: Session = Depends(get_session),
    admin: UserRead = Depends(get_current_admin),
    user_id: int,
):
    """Get detailed user info (including deleted users for audit purposes)."""
    user = get_user_by_id(session, user_id, include_deleted=True)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return AdminUserRead.model_validate(user)


@router.put("/users/{user_id}", response_model=AdminUserRead)
def update_user_by_admin(
    *,
    session: Session = Depends(get_session),
    request: Request,
    admin: UserRead = Depends(get_current_admin),
    user_id: int,
    user_update: AdminUserUpdate,
):
    """Update a user (admin only)."""
    user = get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    changes: dict[str, Any] = {}

    if user_update.first_name is not None:
        changes["first_name"] = {"from": user.first_name, "to": user_update.first_name}
        user.first_name = user_update.first_name

    if user_update.last_name is not None:
        changes["last_name"] = {"from": user.last_name, "to": user_update.last_name}
        user.last_name = user_update.last_name

    if user_update.email is not None and user.email != user_update.email:
        changes["email"] = {"from": user.email, "to": user_update.email}
        user.email = user_update.email
        user.email_confirmed = False

    if user_update.is_admin is not None:
        changes["is_admin"] = {"from": user.is_admin, "to": user_update.is_admin}
        user.is_admin = user_update.is_admin

    if user_update.is_premium is not None:
        changes["is_premium"] = {"from": user.is_premium, "to": user_update.is_premium}
        user.is_premium = user_update.is_premium

    update_user(session, user)

    # Log the admin action
    log_event(
        session,
        action=EventType.ADMIN_USER_UPDATE,
        user_id=user_id,
        details={"changes": changes},
        request=request,
    )

    return AdminUserRead.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_by_admin(
    *,
    session: Session = Depends(get_session),
    request: Request,
    admin: UserRead = Depends(get_current_admin),
    user_id: int,
):
    """Soft delete a user (admin only). Anonymizes personal data."""
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )

    # Fetch user including deleted ones to give proper error message
    user = get_user_by_id(session, user_id, include_deleted=True)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check if already deleted
    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already deleted",
        )

    user_email = user.email

    # Log before soft deletion (so we have the original email)
    log_event(
        session,
        action=EventType.ADMIN_USER_DELETE,
        user_id=user_id,
        details={"deleted_email": user_email},
        request=request,
    )

    soft_delete_user(session, user)


# ============================================================================
# Impersonation
# ============================================================================


@router.post("/impersonate/{user_id}", response_model=ImpersonationResponse)
def start_impersonation(
    *,
    session: Session = Depends(get_session),
    request: Request,
    admin: UserRead = Depends(get_current_admin),
    user_id: int,
):
    """Start impersonating a user. Returns a new token for the target user."""
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot impersonate yourself",
        )

    target_user = get_user_by_id(session, user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Log the impersonation
    log_event(
        session,
        action=EventType.ADMIN_IMPERSONATE_START,
        user_id=user_id,
        details={"target_email": target_user.email},
        request=request,
    )

    # Create token with impersonation info
    target_user_read = UserRead.model_validate(target_user)
    token = create_access_token(admin, impersonating_as=target_user_read)

    return ImpersonationResponse(
        access_token=token.access_token,
        token_parsed=token.token_parsed,
        user=target_user_read,
        message=f"Now impersonating {target_user.email}",
    )


@router.post("/stop-impersonate", response_model=ImpersonationResponse)
def stop_impersonation(
    *,
    session: Session = Depends(get_session),
    request: Request,
    real_admin_id: int | None = Depends(get_real_admin_id),
):
    """
    Stop impersonating and return to admin session.
    Uses the real_admin_id stored in the impersonation token.
    """
    if not real_admin_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not currently impersonating anyone",
        )

    # Fetch the real admin user
    admin_user = get_user_by_id(session, real_admin_id)
    if not admin_user or not admin_user.is_admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin user not found")

    # Log the stop
    log_event(
        session,
        action=EventType.ADMIN_IMPERSONATE_STOP,
        user_id=real_admin_id,
        request=request,
    )

    admin_user_read = UserRead.model_validate(admin_user)
    token = create_access_token(admin_user_read)

    return ImpersonationResponse(
        access_token=token.access_token,
        token_parsed=token.token_parsed,
        user=admin_user_read,
        message="Impersonation stopped",
    )


# ============================================================================
# Event logs
# ============================================================================


@router.get("/events", response_model=EventLogListResponse)
def list_events(
    *,
    session: Session = Depends(get_session),
    admin: UserRead = Depends(get_current_admin),
    user_id: int | None = None,
    action: str | None = Query(None, max_length=100),
    action_prefix: str | None = Query(None, max_length=50),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List event logs with optional filtering."""
    filters = EventLogFilter(
        user_id=user_id,
        action=action,
        action_prefix=action_prefix,
    )

    events, total = get_events(session, filters=filters, limit=limit, offset=offset)

    return EventLogListResponse(
        items=events,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/users/{user_id}/events", response_model=EventLogListResponse)
def get_user_event_log(
    *,
    session: Session = Depends(get_session),
    admin: UserRead = Depends(get_current_admin),
    user_id: int,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Get event log for a specific user."""
    events, total = get_user_events(session, user_id=user_id, limit=limit, offset=offset)

    return EventLogListResponse(
        items=events,
        total=total,
        limit=limit,
        offset=offset,
    )
