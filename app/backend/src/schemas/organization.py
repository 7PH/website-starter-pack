# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Organization-related Pydantic schemas for API requests/responses."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

# User's organization membership (for embedding in UserRead)


class UserOrganizationInfo(BaseModel):
    """Organization info for a user's memberships."""

    organization_id: int
    organization_name: str
    is_admin: bool
    has_premium_seat: bool = False

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


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
    stripe_id: str | None = None
    stripe_premium: bool
    stripe_quota: int
    created_at: datetime | None = None
    deleted_at: datetime | None = None
    member_count: int = 0
    premium_member_count: int = 0
    members: list[OrganizationMemberRead] = []

    class Config:
        from_attributes = True


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
