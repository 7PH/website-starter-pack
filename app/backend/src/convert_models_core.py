# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
"""
Core models for JSON Schema generation.

This module exports CoreModels, a Union of all starterpack schemas.
Projects should import this and combine with their own models in convert-models.py.
"""

from .schemas import (
    AccountDeletionConfirm,
    AccountDeletionInfo,
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
from .schemas.managed_account import (
    ManagedAccountBulkCreate,
    ManagedAccountBulkCreated,
    ManagedAccountCreate,
    ManagedAccountCreated,
    ManagedAccountGroupCreate,
    ManagedAccountGroupRead,
    ManagedAccountGroupUpdate,
    ManagedAccountRead,
    ManagedAccountUpdate,
    PublicPickerEntry,
    PublicPickerPayload,
)
from .schemas.oauth import (
    OAuthCallbackRequest,
    OAuthStatusResponse,
    OAuthUrlResponse,
)
from .schemas.organization import (
    OrganizationAdminBillingRead,
    OrganizationAssignPlanRequest,
    OrganizationBalanceAdjustRequest,
    OrganizationBalanceTransactionRead,
    OrganizationCheckoutRequest,
    OrganizationCheckoutResponse,
    OrganizationCreate,
    OrganizationListResponse,
    OrganizationMemberAdd,
    OrganizationMemberListResponse,
    OrganizationMemberRead,
    OrganizationMemberUpdate,
    OrganizationPlan,
    OrganizationRead,
    OrganizationSubscriptionStatus,
    OrganizationUpdate,
    UserOrganizationInfo,
)
from .schemas.organization_invitation import (
    OrganizationInvitationCreate,
    OrganizationInvitationListResponse,
    OrganizationInvitationRead,
    PendingInvitationPreview,
)
from .schemas.stripe import (
    BillingPortalResponse,
    StripeCheckoutRequest,
    StripeCheckoutResponse,
    StripePlan,
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
    | AccountDeletionInfo
    | AccountDeletionConfirm
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
    | StripePlan
    | StripeCheckoutRequest
    | StripeCheckoutResponse
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
    | OrganizationAdminBillingRead
    | OrganizationBalanceTransactionRead
    | OrganizationBalanceAdjustRequest
    | OrganizationAssignPlanRequest
    # OAuth models
    | OAuthStatusResponse
    | OAuthUrlResponse
    | OAuthCallbackRequest
    # Managed account models
    | ManagedAccountGroupCreate
    | ManagedAccountGroupUpdate
    | ManagedAccountGroupRead
    | ManagedAccountCreate
    | ManagedAccountUpdate
    | ManagedAccountRead
    | ManagedAccountCreated
    | ManagedAccountBulkCreate
    | ManagedAccountBulkCreated
    | PublicPickerEntry
    | PublicPickerPayload
)
