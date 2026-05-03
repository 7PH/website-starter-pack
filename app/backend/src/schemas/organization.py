# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Organization-related Pydantic schemas for API requests/responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# User's organization membership (for embedding in UserRead)


class UserOrganizationInfo(BaseModel):
    """Organization info for a user's memberships."""

    organization_id: int
    organization_name: str
    is_admin: bool
    has_premium_seat: bool = False

    model_config = ConfigDict(from_attributes=True)


# Organization schemas


class OrganizationFieldsMixin(BaseModel):
    """Shared optional fields for organization create/update."""

    description: str | None = None
    phone: str | None = Field(default=None, max_length=50)
    tax_number: str | None = Field(default=None, max_length=100)
    address_line1: str | None = Field(default=None, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, max_length=2)
    custom_data: dict | None = None


class OrganizationCreate(OrganizationFieldsMixin):
    """Schema for creating a new organization."""

    name: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(max_length=255)


class OrganizationUpdate(OrganizationFieldsMixin):
    """Schema for updating an organization."""

    name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class OrganizationMemberRead(BaseModel):
    """Schema for reading organization member info."""

    user_id: int
    email: str
    first_name: str
    last_name: str
    is_admin: bool
    is_premium: bool
    has_premium_seat: bool = False
    joined_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class OrganizationRead(BaseModel):
    """Schema for reading organization info."""

    id: int
    name: str
    email: str
    description: str | None = None
    phone: str | None = None
    tax_number: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    custom_data: dict = {}
    stripe_id: str | None = None
    stripe_premium: bool
    stripe_quota: int
    stripe_dashboard_url: str | None = None
    created_at: datetime | None = None
    deleted_at: datetime | None = None
    member_count: int = 0
    premium_member_count: int = 0
    members: list[OrganizationMemberRead] = []

    model_config = ConfigDict(from_attributes=True)


class OrganizationListResponse(BaseModel):
    """Paginated response for organization list."""

    items: list[OrganizationRead]
    total: int
    page: int
    per_page: int


# Member schemas


class OrganizationMemberAdd(BaseModel):
    """Schema for adding a member by email."""

    email: EmailStr = Field(max_length=255)
    is_admin: bool = False


class OrganizationMemberUpdate(BaseModel):
    """Schema for updating a member's status."""

    is_admin: bool | None = None
    is_premium: bool | None = None


class OrganizationMemberListResponse(BaseModel):
    """Paginated response for member list."""

    items: list[OrganizationMemberRead]
    total: int
    page: int
    per_page: int


# Stripe schemas


class OrganizationPlan(BaseModel):
    """Schema for available organization plans."""

    price_id: str
    name: str
    amount: int
    currency: str
    seats: int
    interval: str  # month, year, week, day


class OrganizationCheckoutRequest(BaseModel):
    """Schema for creating a checkout session."""

    price_id: str


class OrganizationCheckoutResponse(BaseModel):
    """Schema for checkout session response."""

    url: str


class OrganizationSubscriptionStatus(BaseModel):
    """Schema for organization subscription status (synced from Stripe)."""

    stripe_premium: bool
    stripe_quota: int
    cancel_at_period_end: bool = False
    expires_at: str | None = None


# Admin-managed billing schemas


class OrganizationBalanceTransactionRead(BaseModel):
    """A single customer-balance transaction (admin sign convention: +credit / -debit)."""

    id: str
    type: str
    amount_cents: int
    currency: str
    description: str | None = None
    created_at: str


class OrganizationAdminBillingRead(BaseModel):
    """Full admin billing view for an org: balance + plan + transactions."""

    balance_cents: int
    currency: str
    plan: OrganizationPlan | None = None
    cycle_started_at: datetime | None = None
    cycle_end: datetime | None = None
    transactions: list[OrganizationBalanceTransactionRead] = []


class OrganizationBalanceAdjustRequest(BaseModel):
    """Admin records a balance change. amount_cents is signed: +credit, -debit."""

    amount_cents: int = Field(..., description="Positive = credit org, negative = charge org")
    description: str = Field(..., min_length=1, max_length=255)


class OrganizationAssignPlanRequest(BaseModel):
    """Admin assigns a plan to an org (no Stripe subscription is created)."""

    price_id: str = Field(..., min_length=1, max_length=255)


# Invitation schemas


class OrganizationInvitationCreate(BaseModel):
    """Schema for creating an invitation."""

    email: EmailStr = Field(max_length=255)
    is_admin: bool = False


class OrganizationInvitationRead(BaseModel):
    """Schema for reading an invitation.

    `token` is included when the invitation belongs to the current user
    (`/invitations/pending`) so they can Accept/Decline directly. For owner-
    facing lists (per-org), `token` is omitted.
    """

    id: int
    organization_id: int
    organization_name: str | None = None
    email: str
    is_admin_invite: bool
    invited_by_user_id: int | None = None
    invited_by_name: str | None = None
    expires_at: datetime
    created_at: datetime
    token: str | None = None

    model_config = ConfigDict(from_attributes=True)


class OrganizationInvitationListResponse(BaseModel):
    """Response schema for a list of invitations."""

    items: list[OrganizationInvitationRead]


class PendingInvitationPreview(BaseModel):
    """Schema for the Accept/Decline preview page (accessible by token)."""

    organization_name: str
    is_admin_invite: bool
    invited_by_name: str | None = None
    email: str
    expires_at: datetime
