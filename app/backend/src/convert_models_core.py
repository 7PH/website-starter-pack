# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
"""
Core models for JSON Schema generation.

This module exports CoreModels, a Union of all starterpack schemas.
Projects should import this and combine with their own models in convert-models.py.
"""

from .schemas import (
    AuthMessageResponse,
    UserChangeEmail,
    UserChangeInfo,
    UserChangePassword,
    UserCreate,
    UserPasswordResetRequest,
    UserPreviewRead,
    UserRead,
    UserToken,
    UserTokenUpdate,
)
from .schemas.admin import (
    AdminDashboardStats,
    AdminUserListResponse,
    AdminUserRead,
    AdminUserUpdate,
    ImpersonationResponse,
)
from .schemas.backup import (
    BackupInfo,
    BackupListResponse,
)
from .schemas.db_health import (
    DatabaseHealthResponse,
    IndexStats,
    Recommendation,
    TableStats,
)
from .schemas.event_log import (
    EventLogFilter,
    EventLogListResponse,
    EventLogRead,
)
from .schemas.oauth import (
    OAuthCallbackRequest,
    OAuthStatusResponse,
    OAuthUrlResponse,
)
from .schemas.organization import (
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
    PendingInvitationPreview,
    UserOrganizationInfo,
)
from .schemas.stripe import (
    BillingPortalResponse,
    SubscriptionStatus,
)

# Union of all core starterpack models
CoreModels = (
    # Auth models
    AuthMessageResponse
    # User models
    | UserRead
    | UserPreviewRead
    | UserCreate
    | UserChangeEmail
    | UserChangeInfo
    | UserChangePassword
    | UserToken
    | UserTokenUpdate
    | UserPasswordResetRequest
    # Admin models
    | AdminUserRead
    | AdminUserUpdate
    | AdminUserListResponse
    | AdminDashboardStats
    | ImpersonationResponse
    # Event log models
    | EventLogRead
    | EventLogFilter
    | EventLogListResponse
    # Backup models
    | BackupInfo
    | BackupListResponse
    # Stripe models
    | BillingPortalResponse
    | SubscriptionStatus
    # Database health models
    | DatabaseHealthResponse
    | TableStats
    | IndexStats
    | Recommendation
    # Organization models
    | OrganizationRead
    | OrganizationCreate
    | OrganizationUpdate
    | OrganizationListResponse
    | OrganizationMemberRead
    | OrganizationMemberAdd
    | OrganizationMemberUpdate
    | OrganizationMemberListResponse
    | OrganizationPlan
    | OrganizationCheckoutRequest
    | OrganizationCheckoutResponse
    | OrganizationSubscriptionStatus
    | OrganizationInvitationCreate
    | OrganizationInvitationRead
    | OrganizationInvitationListResponse
    | PendingInvitationPreview
    | UserOrganizationInfo
    # OAuth models
    | OAuthStatusResponse
    | OAuthUrlResponse
    | OAuthCallbackRequest
)
