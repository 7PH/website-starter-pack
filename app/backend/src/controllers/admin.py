# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Admin controller for user management, impersonation, and event logs.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..constants import EventType
from ..crud.event_logs import get_events, log_event
from ..crud.organizations import get_user_organizations
from ..crud.users import get_user_by_id, soft_delete_user, update_user
from ..helpers.auth import create_access_token, get_current_admin, get_real_admin_id, get_user_or_404
from ..helpers.db import get_session
from ..models.user import UserBase
from ..schemas.admin import (
    AdminDashboardStats,
    AdminUserListResponse,
    AdminUserRead,
    AdminUserUpdate,
    ImpersonationRequest,
    ImpersonationResponse,
)
from ..schemas.event_log import EventLogFilter, EventLogListResponse
from ..schemas.user import UserRead
from ..schemas.user_ext import UserCustomData

router = APIRouter(prefix="/admin")


# ============================================================================
# Dashboard
# ============================================================================


@router.get("/stats", response_model=AdminDashboardStats)
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
        clauses = [
            UserBase.email.ilike(search_pattern),
            UserBase.first_name.ilike(search_pattern),
            UserBase.last_name.ilike(search_pattern),
        ]
        # Numeric search → also match by id, so admins can find email-less
        # users (access-code, deleted) by their ID directly.
        if search.isdigit():
            clauses.append(UserBase.id == int(search))
        query = query.filter(or_(*clauses))

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
    user = get_user_or_404(session, user_id, include_deleted=True)
    user_data = AdminUserRead.model_validate(user)
    memberships = get_user_organizations(session, user_id)
    user_data.organizations = [
        {
            "organization_id": m.organization_id,
            "organization_name": m.organization.name,
            "is_admin": m.is_admin,
            "has_premium_seat": m.has_premium_seat,
        }
        for m in memberships
    ]
    return user_data


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
    user = get_user_or_404(session, user_id)

    changes: dict[str, Any] = {}

    for field in ("first_name", "last_name", "display_name", "is_admin", "is_premium"):
        new_value = getattr(user_update, field)
        if new_value is None:
            continue
        changes[field] = {"from": getattr(user, field), "to": new_value}
        setattr(user, field, new_value)

    if user_update.email is not None and user.email != user_update.email:
        changes["email"] = {"from": user.email, "to": user_update.email}
        user.email = user_update.email
        user.email_confirmed = False

    if user_update.custom_data is not None:
        incoming = user_update.custom_data.model_dump(exclude_none=True)
        merged = {**(user.custom_data or {}), **incoming}
        new_custom_data = UserCustomData(**merged).model_dump(exclude_none=True)
        if new_custom_data != (user.custom_data or {}):
            changes["custom_data"] = {"from": user.custom_data or {}, "to": new_custom_data}
            user.custom_data = new_custom_data

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
    user = get_user_or_404(session, user_id, include_deleted=True)

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


@router.post("/impersonations", response_model=ImpersonationResponse)
def start_impersonation(
    *,
    session: Session = Depends(get_session),
    request: Request,
    admin: UserRead = Depends(get_current_admin),
    body: ImpersonationRequest,
):
    """Start impersonating a user. Returns a new token for the target user."""
    user_id = body.user_id
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot impersonate yourself",
        )

    target_user = get_user_or_404(session, user_id)

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


@router.delete("/impersonations", response_model=ImpersonationResponse)
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
    events, total = get_events(session, filters=EventLogFilter(user_id=user_id), limit=limit, offset=offset)

    return EventLogListResponse(
        items=events,
        total=total,
        limit=limit,
        offset=offset,
    )
