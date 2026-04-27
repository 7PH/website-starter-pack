# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Organizations controller for org management, member management, and subscriptions.
"""

import logging
from datetime import UTC, datetime
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from ..constants import (
    ORG_INVITATION_EXPIRY_DAYS,
    ORG_INVITATIONS_ENABLED,
    ORG_MAX_MEMBERS,
    ORG_MAX_PER_USER,
    ORG_SELF_SERVICE_CREATION,
    ORG_SELF_SERVICE_SUBSCRIPTIONS,
    ORG_STRIPE_PRICE_IDS,
    PUBLIC_URL,
    STRIPE_ENABLED,
    EventType,
)
from ..crud import organization_invitations as invitations_crud
from ..crud.event_logs import log_event
from ..crud.organizations import (
    add_organization_member,
    count_org_admins,
    count_org_premium_members,
    count_organization_members,
    count_user_organizations,
    create_organization,
    get_org_member_counts,
    get_organization_by_id,
    get_organization_members,
    get_organizations,
    get_user_org_membership,
    is_org_email_taken,
    remove_organization_member,
    reset_org_members_premium,
    soft_delete_organization,
    update_organization,
    update_organization_member,
)
from ..crud.users import get_user_by_email, get_user_by_id, update_user_premium_cache
from ..helpers import stripe as stripe_helper
from ..helpers.auth import get_current_admin, get_current_nonmanaged_user, get_current_user
from ..helpers.db import get_session
from ..helpers.email import send_organization_invitation_email
from ..models.organization import OrganizationBase, OrganizationInvitationBase, UserOrganizationBase
from ..models.user import UserBase
from ..schemas.organization import (
    OrganizationAdminBillingRead,
    OrganizationAssignPlanRequest,
    OrganizationBalanceAdjustRequest,
    OrganizationBalanceTransactionRead,
    OrganizationCheckoutRequest,
    OrganizationCheckoutResponse,
    OrganizationCreate,
    OrganizationInvitationCreate,
    OrganizationInvitationListResponse,
    OrganizationInvitationRead,
    OrganizationListResponse,
    OrganizationMemberAdd,
    OrganizationMemberListResponse,
    OrganizationMemberRead,
    OrganizationMemberUpdate,
    OrganizationPlan,
    OrganizationRead,
    OrganizationSubscriptionStatus,
    OrganizationUpdate,
)
from ..schemas.organization_ext import OrganizationCustomData
from ..schemas.stripe import BillingPortalResponse
from ..schemas.user import UserRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/organizations")

# Default limit for fetching all members of an org in detail view
ORG_DETAIL_MEMBER_LIMIT = 100


# ============================================================================
# Helpers
# ============================================================================


def _validate_redirect_url(url: str, public_url: str | None = None) -> str:
    """Validate and sanitize a redirect URL. Returns empty string if invalid."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        # Must be http or https
        if parsed.scheme not in ("http", "https"):
            return ""
        # Must have a valid netloc (host)
        if not parsed.netloc:
            return ""
        # If PUBLIC_URL is set, validate origin matches
        if public_url:
            public_parsed = urlparse(public_url)
            if parsed.netloc != public_parsed.netloc:
                logger.warning(f"Redirect URL host mismatch: {parsed.netloc} != {public_parsed.netloc}")
                return ""
        return url
    except Exception:
        return ""


def _check_org_access(
    session: Session,
    org_id: int,
    user: UserRead,
    require_admin: bool = False,
) -> OrganizationBase:
    """Check if user has access to org. Returns the org or raises 404/403."""
    org = get_organization_by_id(session, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    # System admins have full access
    if user.is_admin:
        return org

    # Check org membership
    membership = get_user_org_membership(session, user.id, org_id)
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if require_admin and not membership.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Org admin access required")

    return org


def _check_not_last_admin(session: Session, org_id: int, membership: UserOrganizationBase, action: str = "remove") -> None:
    """Check if the given member is the last admin. Raises 400 if so."""
    if membership.is_admin:
        admin_count = count_org_admins(session, org_id)
        if admin_count <= 1:
            if action == "leave":
                detail = "Cannot leave as the last admin. Promote another member first."
            elif action == "demote":
                detail = "Cannot demote the last admin"
            else:
                detail = "Cannot remove the last admin"
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def _membership_to_read(membership: UserOrganizationBase, user: UserBase) -> OrganizationMemberRead:
    """Convert membership + user to OrganizationMemberRead schema."""
    return OrganizationMemberRead(
        user_id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_admin=membership.is_admin,
        is_premium=user.is_premium,
        has_premium_seat=membership.has_premium_seat,
        joined_at=membership.created_at,
    )


def _build_org_read(
    org: OrganizationBase,
    member_count: int,
    premium_count: int,
    members: list[OrganizationMemberRead] | None = None,
) -> OrganizationRead:
    """Build OrganizationRead schema from org model and counts."""
    return OrganizationRead(
        id=org.id,
        name=org.name,
        email=org.email,
        description=org.description,
        phone=org.phone,
        tax_number=org.tax_number,
        address_line1=org.address_line1,
        address_line2=org.address_line2,
        city=org.city,
        state=org.state,
        postal_code=org.postal_code,
        country=org.country,
        stripe_id=org.stripe_id,
        stripe_premium=org.stripe_premium,
        stripe_quota=org.stripe_quota,
        stripe_dashboard_url=stripe_helper.get_dashboard_customer_url(org.stripe_id) if org.stripe_id else None,
        created_at=org.created_at,
        custom_data=org.custom_data or {},
        deleted_at=org.deleted_at,
        member_count=member_count,
        premium_member_count=premium_count,
        members=members or [],
    )


def _org_to_read(session: Session, org: OrganizationBase) -> OrganizationRead:
    """Convert org model to read schema with full member list."""
    memberships, total = get_organization_members(session, org.id, page=1, per_page=ORG_DETAIL_MEMBER_LIMIT)
    members_list = [_membership_to_read(m, m.user) for m in memberships if m.user]
    premium_count = sum(1 for m in memberships if m.has_premium_seat)
    return _build_org_read(org, total, premium_count, members_list)


def _org_to_summary(org: OrganizationBase, member_count: int, premium_count: int) -> OrganizationRead:
    """Convert org model to summary schema (no member list, uses pre-fetched counts)."""
    return _build_org_read(org, member_count, premium_count)


# ============================================================================
# Organization CRUD
# ============================================================================


@router.get("", response_model=OrganizationListResponse)
def list_organizations(
    *,
    session: Session = Depends(get_session),
    _admin: UserRead = Depends(get_current_admin),  # Used for auth only
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
):
    """List all organizations (system admin only)."""
    # Search is applied at SQL level for efficiency
    orgs, total = get_organizations(session, page=page, per_page=per_page, search=search)

    # Batch-fetch member counts to avoid N+1 queries
    org_ids = [org.id for org in orgs]
    counts = get_org_member_counts(session, org_ids)

    items = [
        _org_to_summary(org, *counts.get(org.id, (0, 0)))
        for org in orgs
    ]

    return OrganizationListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
def create_new_organization(
    *,
    session: Session = Depends(get_session),
    request: Request,
    user: UserRead = Depends(get_current_nonmanaged_user),
    org_data: OrganizationCreate,
):
    """Create a new organization. Creator becomes first admin.

    Access:
    - System admins can always create organizations
    - Regular users can create if ORG_SELF_SERVICE_CREATION is enabled
    """
    # Block non-admins if self-service creation is disabled
    if not ORG_SELF_SERVICE_CREATION and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization creation is disabled",
        )

    # Check max orgs per user (skip for system admins)
    if not user.is_admin:
        user_org_count = count_user_organizations(session, user.id)
        if user_org_count >= ORG_MAX_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum of {ORG_MAX_PER_USER} organization(s) reached",
            )

    # Check if email is taken
    if is_org_email_taken(session, org_data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An organization with this email already exists",
        )

    # Validate custom_data against project schema
    custom_data = {}
    if org_data.custom_data:
        custom_data = OrganizationCustomData(**org_data.custom_data).model_dump(exclude_none=True)

    # Create the organization
    org = OrganizationBase(
        name=org_data.name,
        email=org_data.email,
        description=org_data.description,
        phone=org_data.phone,
        tax_number=org_data.tax_number,
        address_line1=org_data.address_line1,
        address_line2=org_data.address_line2,
        city=org_data.city,
        state=org_data.state,
        postal_code=org_data.postal_code,
        country=org_data.country,
        custom_data=custom_data,
    )
    org = create_organization(session, org)

    # Add creator as first admin
    add_organization_member(session, user.id, org.id, is_admin=True)

    # Log event
    log_event(
        session,
        action=EventType.ORG_CREATED,
        user_id=user.id,
        details={"org_id": org.id, "org_name": org.name},
        request=request,
    )

    return _org_to_read(session, org)


# ============================================================================
# Stripe Plans (must be before /{org_id} to avoid route conflicts)
# ============================================================================


@router.get("/plans", response_model=list[OrganizationPlan])
def get_organization_plans():
    """Get available organization subscription plans from Stripe."""
    if not STRIPE_ENABLED or not stripe_helper.is_enabled():
        return []

    if not ORG_STRIPE_PRICE_IDS:
        return []

    plans = []
    for price_id in ORG_STRIPE_PRICE_IDS:
        plan = stripe_helper.get_price_details(price_id)
        if plan:
            plans.append(OrganizationPlan(**plan))

    return plans


@router.get("/{org_id}", response_model=OrganizationRead)
def get_organization(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_current_user),
    org_id: int,
):
    """Get organization details. Accessible by any member of the org (or system admin)."""
    org = _check_org_access(session, org_id, user, require_admin=False)
    return _org_to_read(session, org)


@router.patch("/{org_id}", response_model=OrganizationRead)
def update_org(
    *,
    session: Session = Depends(get_session),
    request: Request,
    user: UserRead = Depends(get_current_user),
    org_id: int,
    org_data: OrganizationUpdate,
):
    """Update organization details. Accessible by system admin or org admin."""
    org = _check_org_access(session, org_id, user, require_admin=True)

    changes = {}

    if org_data.name is not None and org_data.name != org.name:
        changes["name"] = {"from": org.name, "to": org_data.name}
        org.name = org_data.name

    if org_data.email is not None and org_data.email != org.email:
        if is_org_email_taken(session, org_data.email, exclude_org_id=org.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An organization with this email already exists",
            )
        changes["email"] = {"from": org.email, "to": org_data.email}
        org.email = org_data.email

    # Update optional fields
    optional_fields = [
        'description', 'phone', 'tax_number', 'address_line1',
        'address_line2', 'city', 'state', 'postal_code', 'country'
    ]
    for field in optional_fields:
        value = getattr(org_data, field, None)
        if value is not None:
            setattr(org, field, value)

    if org_data.custom_data is not None:
        merged = {**(org.custom_data or {}), **org_data.custom_data}
        org.custom_data = OrganizationCustomData(**merged).model_dump(exclude_none=True)

    update_organization(session, org)

    if changes:
        log_event(
            session,
            action=EventType.ORG_UPDATED,
            user_id=user.id,
            details={"org_id": org.id, "changes": changes},
            request=request,
        )

    return _org_to_read(session, org)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_org(
    *,
    session: Session = Depends(get_session),
    request: Request,
    admin: UserRead = Depends(get_current_admin),
    org_id: int,
):
    """Soft delete an organization (system admin only). Resets all members' premium."""
    org = get_organization_by_id(session, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    if org.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization is already deleted",
        )

    org_name = org.name

    # Reset premium for all members and update their cached premium status
    affected_user_ids = reset_org_members_premium(session, org.id)
    for user_id in affected_user_ids:
        update_user_premium_cache(session, user_id)

    # Log before deletion
    log_event(
        session,
        action=EventType.ORG_DELETED,
        user_id=admin.id,
        details={"org_id": org.id, "org_name": org_name},
        request=request,
    )

    soft_delete_organization(session, org)


# ============================================================================
# Member Management
# ============================================================================


@router.post("/{org_id}/members", response_model=OrganizationMemberRead, status_code=status.HTTP_201_CREATED)
def add_member(
    *,
    session: Session = Depends(get_session),
    request: Request,
    user: UserRead = Depends(get_current_nonmanaged_user),
    org_id: int,
    member_data: OrganizationMemberAdd,
):
    """Add a member by email. Org admin only.

    When `ORG_INVITATIONS_ENABLED` is on, this endpoint is disabled and clients
    must use the invitation flow (`POST /organizations/{id}/invitations`).
    """
    if ORG_INVITATIONS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Direct-add is disabled. Use the invitation endpoint instead.",
        )

    org = _check_org_access(session, org_id, user, require_admin=True)

    # Find user by email - use same message whether user exists or not (security)
    target_user = get_user_by_email(session, member_data.email)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to add member. Please verify the email address.",
        )

    # Check if already a member
    existing = get_user_org_membership(session, target_user.id, org.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this organization",
        )

    # Check max orgs per user
    user_org_count = count_user_organizations(session, target_user.id)
    if user_org_count >= ORG_MAX_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User has reached the maximum of {ORG_MAX_PER_USER} organization(s)",
        )

    # Check max members per org
    org_member_count = count_organization_members(session, org.id)
    if org_member_count >= ORG_MAX_MEMBERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization has reached the maximum of {ORG_MAX_MEMBERS} member(s)",
        )

    # Add member
    membership = add_organization_member(session, target_user.id, org.id, is_admin=member_data.is_admin)

    log_event(
        session,
        action=EventType.ORG_MEMBER_ADDED,
        user_id=user.id,
        details={"org_id": org.id, "target_user_id": target_user.id, "is_admin": member_data.is_admin},
        request=request,
    )

    return _membership_to_read(membership, target_user)


@router.get("/{org_id}/members", response_model=OrganizationMemberListResponse)
def list_members(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_current_user),
    org_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """List organization members. Org admin only."""
    _check_org_access(session, org_id, user, require_admin=True)

    memberships, total = get_organization_members(session, org_id, page=page, per_page=per_page)

    items = [_membership_to_read(m, m.user) for m in memberships if m.user]

    return OrganizationMemberListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{org_id}/members/{member_id}", response_model=OrganizationMemberRead)
def get_member(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_current_user),
    org_id: int,
    member_id: int,
):
    """Get member details. Org admin only."""
    _check_org_access(session, org_id, user, require_admin=True)

    membership = get_user_org_membership(session, member_id, org_id)
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    target_user = get_user_by_id(session, member_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    return _membership_to_read(membership, target_user)


def _update_member_admin_status(
    session: Session,
    request: Request,
    org: OrganizationBase,
    membership: UserOrganizationBase,
    user: UserRead,
    new_is_admin: bool,
) -> None:
    """Handle admin status change for a member."""
    if new_is_admin == membership.is_admin:
        return

    # Check if demoting last admin
    if not new_is_admin:
        _check_not_last_admin(session, org.id, membership, action="demote")

    membership.is_admin = new_is_admin
    update_organization_member(session, membership)

    log_event(
        session,
        action=EventType.ORG_MEMBER_ADMIN_CHANGED,
        user_id=user.id,
        details={"org_id": org.id, "target_user_id": membership.user_id, "is_admin": new_is_admin},
        request=request,
    )


def _update_member_premium_status(
    session: Session,
    request: Request,
    org: OrganizationBase,
    membership: UserOrganizationBase,
    target_user: UserBase,
    user: UserRead,
    new_has_premium: bool,
) -> None:
    """Handle premium seat change for a member."""
    if new_has_premium == membership.has_premium_seat:
        return

    if new_has_premium:
        current_premium = count_org_premium_members(session, org.id)
        if current_premium >= org.stripe_quota:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Organization has reached its premium seat limit ({org.stripe_quota})",
            )

    membership.has_premium_seat = new_has_premium
    session.flush()  # Flush so update_user_premium_cache sees the new has_premium_seat value
    update_user_premium_cache(session, target_user.id)

    log_event(
        session,
        action=EventType.ORG_MEMBER_PREMIUM_CHANGED,
        user_id=user.id,
        details={"org_id": org.id, "target_user_id": target_user.id, "has_premium_seat": new_has_premium},
        request=request,
    )


@router.patch("/{org_id}/members/{member_id}", response_model=OrganizationMemberRead)
def update_member(
    *,
    session: Session = Depends(get_session),
    request: Request,
    user: UserRead = Depends(get_current_user),
    org_id: int,
    member_id: int,
    member_data: OrganizationMemberUpdate,
):
    """Update member status (is_admin, is_premium). Org admin only."""
    org = _check_org_access(session, org_id, user, require_admin=True)

    membership = get_user_org_membership(session, member_id, org_id)
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    target_user = get_user_by_id(session, member_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if member_data.is_admin is not None:
        _update_member_admin_status(session, request, org, membership, user, member_data.is_admin)

    if member_data.is_premium is not None:
        _update_member_premium_status(session, request, org, membership, target_user, user, member_data.is_premium)

    session.refresh(target_user)
    return _membership_to_read(membership, target_user)


@router.delete("/{org_id}/members/me", status_code=status.HTTP_204_NO_CONTENT)
def leave_organization(
    *,
    session: Session = Depends(get_session),
    request: Request,
    user: UserRead = Depends(get_current_user),
    org_id: int,
):
    """Leave an organization voluntarily."""
    org = get_organization_by_id(session, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    membership = get_user_org_membership(session, user.id, org_id)
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You are not a member of this organization")

    # Check if last admin
    _check_not_last_admin(session, org.id, membership, action="leave")

    log_event(
        session,
        action=EventType.ORG_MEMBER_LEFT,
        user_id=user.id,
        details={"org_id": org.id},
        request=request,
    )

    remove_organization_member(session, membership)

    # Recalculate user's premium status after leaving org
    update_user_premium_cache(session, user.id)


@router.delete("/{org_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    *,
    session: Session = Depends(get_session),
    request: Request,
    user: UserRead = Depends(get_current_user),
    org_id: int,
    member_id: int,
):
    """Remove a member from the organization. Org admin only."""
    org = _check_org_access(session, org_id, user, require_admin=True)

    membership = get_user_org_membership(session, member_id, org_id)
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    # Check if removing last admin
    _check_not_last_admin(session, org.id, membership, action="remove")

    log_event(
        session,
        action=EventType.ORG_MEMBER_REMOVED,
        user_id=user.id,
        details={"org_id": org.id, "target_user_id": member_id},
        request=request,
    )

    remove_organization_member(session, membership)

    # Recalculate user's premium status after removal
    update_user_premium_cache(session, member_id)


# ============================================================================
# Stripe Integration (when STRIPE_ENABLED)
# ============================================================================


@router.post("/{org_id}/checkout", response_model=OrganizationCheckoutResponse)
def create_org_checkout(
    *,
    session: Session = Depends(get_session),
    request: Request,
    user: UserRead = Depends(get_current_nonmanaged_user),
    org_id: int,
    checkout_data: OrganizationCheckoutRequest,
):
    """Create a Stripe checkout session for org subscription. Org admin only."""
    if not STRIPE_ENABLED or not stripe_helper.is_enabled():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Billing not enabled")

    # Block self-service if disabled (unless user is app admin)
    if not ORG_SELF_SERVICE_SUBSCRIPTIONS and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Self-service subscriptions are disabled")

    org = _check_org_access(session, org_id, user, require_admin=True)

    # Validate price_id is an allowed org price
    if checkout_data.price_id not in ORG_STRIPE_PRICE_IDS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid price ID")

    # Create Stripe customer for org if needed
    if not org.stripe_id:
        org.stripe_id = stripe_helper.sync_org_customer(
            org_id=org.id,
            email=org.email,
            name=org.name,
        )
        update_organization(session, org)

    # Build return URLs with validation to prevent open redirect
    origin = request.headers.get("origin", "")
    public_url = PUBLIC_URL or _validate_redirect_url(origin) or ""
    if not public_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid origin for redirect")
    org_path = f"/admin/organizations/{org_id}" if user.is_admin else f"/organizations/{org_id}"
    success_url = f"{public_url}{org_path}?subscription=success"
    cancel_url = f"{public_url}{org_path}?subscription=canceled"

    url = stripe_helper.create_checkout_session(
        stripe_customer_id=org.stripe_id,
        price_id=checkout_data.price_id,
        success_url=success_url,
        cancel_url=cancel_url,
    )

    log_event(
        session,
        action=EventType.ORG_SUBSCRIPTION_CREATED,
        user_id=user.id,
        details={"org_id": org.id, "price_id": checkout_data.price_id},
        request=request,
    )

    return OrganizationCheckoutResponse(url=url)


@router.get("/{org_id}/portal", response_model=BillingPortalResponse)
def get_org_billing_portal(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_current_nonmanaged_user),
    org_id: int,
    return_url: str = Query(..., description="URL to return to after portal session"),
):
    """Get a Stripe billing portal URL for the organization. Org admin only."""
    if not STRIPE_ENABLED or not stripe_helper.is_enabled():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Billing not enabled")

    # Block self-service if disabled (unless user is app admin)
    if not ORG_SELF_SERVICE_SUBSCRIPTIONS and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Self-service subscriptions are disabled")

    org = _check_org_access(session, org_id, user, require_admin=True)

    if not org.stripe_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization has no billing account",
        )

    # Validate return_url to prevent open redirect
    validated_url = _validate_redirect_url(return_url, PUBLIC_URL)
    if not validated_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid return URL")

    url = stripe_helper.create_billing_portal_session(
        stripe_customer_id=org.stripe_id,
        return_url=validated_url,
    )

    return BillingPortalResponse(url=url)


@router.get("/{org_id}/subscription", response_model=OrganizationSubscriptionStatus)
def get_org_subscription(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_current_user),
    org_id: int,
):
    """
    Get organization subscription status, syncing with Stripe.
    Always queries Stripe API for accuracy and syncs DB if status differs.
    Org admin only.
    """
    if not STRIPE_ENABLED or not stripe_helper.is_enabled():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Billing not enabled")

    org = _check_org_access(session, org_id, user, require_admin=True)

    if not org.stripe_id:
        return OrganizationSubscriptionStatus(
            stripe_premium=org.stripe_premium,
            stripe_quota=org.stripe_quota,
        )

    # Query Stripe for current status
    stripe_status = stripe_helper.get_org_subscription_status(org.stripe_id)

    # Sync DB if status differs (handles webhook failures)
    if (
        stripe_status["stripe_premium"] != org.stripe_premium
        or stripe_status["stripe_quota"] != org.stripe_quota
    ):
        # Store previous premium status before updating
        was_premium = org.stripe_premium

        org.stripe_premium = stripe_status["stripe_premium"]
        org.stripe_quota = stripe_status["stripe_quota"]
        update_organization(session, org)

        # If subscription was cancelled, clear all premium seats
        if not stripe_status["stripe_premium"] and was_premium:
            affected_user_ids = reset_org_members_premium(session, org.id)
            for uid in affected_user_ids:
                update_user_premium_cache(session, uid)

        logger.info(f"Synced org {org.id} subscription: premium={org.stripe_premium}, quota={org.stripe_quota}")

    return OrganizationSubscriptionStatus(**stripe_status)


# ============================================================================
# Email Invitations (when ORG_INVITATIONS_ENABLED)
# ============================================================================


def _invitation_to_read(invitation: OrganizationInvitationBase) -> OrganizationInvitationRead:
    inviter = invitation.invited_by
    inviter_name = None
    if inviter:
        inviter_name = f"{inviter.first_name} {inviter.last_name}".strip() or inviter.email
    return OrganizationInvitationRead(
        id=invitation.id,
        organization_id=invitation.organization_id,
        organization_name=invitation.organization.name if invitation.organization else None,
        email=invitation.email,
        is_admin_invite=invitation.is_admin_invite,
        invited_by_user_id=invitation.invited_by_user_id,
        invited_by_name=inviter_name,
        expires_at=invitation.expires_at,
        created_at=invitation.created_at,
    )


@router.post(
    "/{org_id}/invitations",
    response_model=OrganizationInvitationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_invitation(
    *,
    session: Session = Depends(get_session),
    request: Request,
    user: UserRead = Depends(get_current_nonmanaged_user),
    org_id: int,
    invitation_data: OrganizationInvitationCreate,
):
    """Invite a new member by email. Org owner only."""
    if not ORG_INVITATIONS_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitations are disabled")

    org = _check_org_access(session, org_id, user, require_admin=True)
    if org.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization is deleted")

    existing_user = get_user_by_email(session, invitation_data.email)
    if existing_user and get_user_org_membership(session, existing_user.id, org.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this organization",
        )

    if invitations_crud.get_pending_invitation(session, org.id, invitation_data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An invitation is already pending for this email",
        )

    org_member_count = count_organization_members(session, org.id)
    if org_member_count >= ORG_MAX_MEMBERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization has reached the maximum of {ORG_MAX_MEMBERS} member(s)",
        )

    invitation = invitations_crud.create_invitation(
        session,
        organization_id=org.id,
        email=invitation_data.email,
        is_admin_invite=invitation_data.is_admin,
        invited_by_user_id=user.id,
        expiry_days=ORG_INVITATION_EXPIRY_DAYS,
    )

    invitation_link = f"{PUBLIC_URL.rstrip('/')}/invitations/{invitation.token}" if PUBLIC_URL else f"/invitations/{invitation.token}"
    inviter_name = f"{user.first_name} {user.last_name}".strip() or user.email
    send_organization_invitation_email(
        to_email=invitation.email,
        organization_name=org.name,
        inviter_name=inviter_name,
        invitation_link=invitation_link,
        is_admin_invite=invitation.is_admin_invite,
    )

    log_event(
        session,
        action=EventType.ORG_INVITATION_SENT,
        user_id=user.id,
        details={"org_id": org.id, "invited_email": invitation.email, "is_admin": invitation.is_admin_invite},
        request=request,
    )

    # Reload with relationships
    invitation = invitations_crud.get_invitation_by_token(session, invitation.token) or invitation
    return _invitation_to_read(invitation)


@router.get("/{org_id}/invitations", response_model=OrganizationInvitationListResponse)
def list_org_invitations(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_current_user),
    org_id: int,
):
    """List pending invitations for an organization. Org owner only."""
    if not ORG_INVITATIONS_ENABLED:
        return OrganizationInvitationListResponse(items=[])
    _check_org_access(session, org_id, user, require_admin=True)
    pending = invitations_crud.list_org_pending_invitations(session, org_id)
    return OrganizationInvitationListResponse(items=[_invitation_to_read(inv) for inv in pending])


@router.delete("/{org_id}/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_invitation(
    *,
    session: Session = Depends(get_session),
    request: Request,
    user: UserRead = Depends(get_current_user),
    org_id: int,
    invitation_id: int,
):
    """Cancel a pending invitation. Org owner only."""
    if not ORG_INVITATIONS_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitations are disabled")
    _check_org_access(session, org_id, user, require_admin=True)
    invitation = invitations_crud.get_invitation_by_id(session, invitation_id)
    if not invitation or invitation.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

    log_event(
        session,
        action=EventType.ORG_INVITATION_CANCELED,
        user_id=user.id,
        details={"org_id": org_id, "invited_email": invitation.email},
        request=request,
    )
    invitations_crud.delete_invitation(session, invitation)


# ============================================================================
# Admin-Managed Billing (bank-transfer orgs)
#
# Runs alongside the self-serve checkout flow above. System admins can:
#   - see a running balance ledger (Stripe customer.balance, admin-signed)
#   - record a payment received or a manual debit
#   - assign/unassign a plan without ever creating a Stripe subscription
#     (orgs must not see Stripe-generated invoices).
# ============================================================================


def _ensure_org_stripe_customer(session: Session, org: OrganizationBase) -> None:
    """Create a Stripe customer for the org if it doesn't have one yet."""
    if org.stripe_id:
        return
    org.stripe_id = stripe_helper.sync_org_customer(
        org_id=org.id,
        email=org.email,
        name=org.name,
    )
    update_organization(session, org)


def _build_admin_billing_read(org: OrganizationBase) -> OrganizationAdminBillingRead:
    """Assemble the admin billing view from Stripe + org row."""
    plan: OrganizationPlan | None = None
    if org.billing_price_id:
        price = stripe_helper.get_price_details(org.billing_price_id)
        if price:
            plan = OrganizationPlan(**price)

    if org.stripe_id:
        balance = stripe_helper.get_org_balance(org.stripe_id)
        txs = [
            OrganizationBalanceTransactionRead(**tx)
            for tx in stripe_helper.list_org_balance_transactions(org.stripe_id, limit=50)
        ]
    else:
        balance = {"balance_cents": 0, "currency": plan.currency if plan else "eur"}
        txs = []

    return OrganizationAdminBillingRead(
        balance_cents=balance["balance_cents"],
        currency=balance["currency"],
        plan=plan,
        cycle_started_at=org.billing_cycle_started_at,
        cycle_end=org.billing_cycle_end,
        transactions=txs,
    )


@router.get("/{org_id}/admin-billing", response_model=OrganizationAdminBillingRead)
def get_admin_billing(
    *,
    session: Session = Depends(get_session),
    _admin: UserRead = Depends(get_current_admin),
    org_id: int,
):
    """Get admin billing view for an org (system admin only)."""
    if not STRIPE_ENABLED or not stripe_helper.is_enabled():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Billing not enabled")

    org = get_organization_by_id(session, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    return _build_admin_billing_read(org)


@router.post("/{org_id}/admin-billing/adjust", response_model=OrganizationAdminBillingRead)
def adjust_admin_billing(
    *,
    session: Session = Depends(get_session),
    request: Request,
    admin: UserRead = Depends(get_current_admin),
    org_id: int,
    adjustment: OrganizationBalanceAdjustRequest,
):
    """Record a balance change (positive = credit org, negative = charge org)."""
    if not STRIPE_ENABLED or not stripe_helper.is_enabled():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Billing not enabled")

    org = get_organization_by_id(session, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    _ensure_org_stripe_customer(session, org)

    stripe_helper.adjust_org_balance(
        stripe_customer_id=org.stripe_id,
        amount_cents=adjustment.amount_cents,
        description=adjustment.description,
    )

    log_event(
        session,
        action=EventType.ORG_BALANCE_ADJUSTED,
        user_id=admin.id,
        details={
            "org_id": org.id,
            "amount_cents": adjustment.amount_cents,
            "description": adjustment.description,
        },
        request=request,
    )

    return _build_admin_billing_read(org)


@router.post("/{org_id}/admin-billing/plan", response_model=OrganizationAdminBillingRead)
def assign_admin_plan(
    *,
    session: Session = Depends(get_session),
    request: Request,
    admin: UserRead = Depends(get_current_admin),
    org_id: int,
    assignment: OrganizationAssignPlanRequest,
):
    """Assign a plan to an org without creating a Stripe subscription."""
    if not STRIPE_ENABLED or not stripe_helper.is_enabled():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Billing not enabled")

    if assignment.price_id not in ORG_STRIPE_PRICE_IDS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid price ID")

    org = get_organization_by_id(session, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    price = stripe_helper.get_price_details(assignment.price_id)
    if not price:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to fetch plan details")

    _ensure_org_stripe_customer(session, org)

    now = datetime.now(UTC)
    org.billing_price_id = assignment.price_id
    org.billing_cycle_started_at = now
    org.billing_cycle_end = stripe_helper.compute_next_cycle_end(price["interval"], now)
    org.stripe_premium = True
    org.stripe_quota = price["seats"]
    update_organization(session, org)

    log_event(
        session,
        action=EventType.ORG_SUBSCRIPTION_CREATED,
        user_id=admin.id,
        details={"org_id": org.id, "price_id": assignment.price_id, "admin_assigned": True},
        request=request,
    )

    return _build_admin_billing_read(org)


@router.delete("/{org_id}/admin-billing/plan", response_model=OrganizationAdminBillingRead)
def unassign_admin_plan(
    *,
    session: Session = Depends(get_session),
    request: Request,
    admin: UserRead = Depends(get_current_admin),
    org_id: int,
):
    """Unassign the admin-managed plan. Revokes premium for all members."""
    if not STRIPE_ENABLED or not stripe_helper.is_enabled():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Billing not enabled")

    org = get_organization_by_id(session, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    was_assigned = org.billing_price_id is not None

    org.billing_price_id = None
    org.billing_cycle_started_at = None
    org.billing_cycle_end = None
    org.stripe_premium = False
    org.stripe_quota = 0
    update_organization(session, org)

    affected_user_ids = reset_org_members_premium(session, org.id)
    for uid in affected_user_ids:
        update_user_premium_cache(session, uid)

    if was_assigned:
        log_event(
            session,
            action=EventType.ORG_SUBSCRIPTION_CANCELED,
            user_id=admin.id,
            details={"org_id": org.id, "admin_assigned": True},
            request=request,
        )

    return _build_admin_billing_read(org)
