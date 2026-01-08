# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Pydantic schemas for API requests/responses."""

from .admin import (
    AdminDashboardStats,
    AdminUserListResponse,
    AdminUserRead,
    AdminUserUpdate,
    ImpersonationResponse,
)
from .backup import (
    BackupInfo,
    BackupListResponse,
)
from .base import PaginatedItems
from .db_health import (
    DatabaseHealthResponse,
    IndexStats,
    Recommendation,
    TableStats,
)
from .event_log import (
    EventLogCreate,
    EventLogFilter,
    EventLogListResponse,
    EventLogRead,
)
from .stripe import (
    BillingPortalResponse,
    SubscriptionStatus,
    WebhookResponse,
)
from .user import (
    AuthMessageResponse,
    EmailChangeConfirm,
    EmailVerificationConfirm,
    PasswordResetConfirmJWT,
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

__all__ = [
    # Admin schemas
    "AdminDashboardStats",
    "AdminUserListResponse",
    "AdminUserRead",
    "AdminUserUpdate",
    "ImpersonationResponse",
    # Backup schemas
    "BackupInfo",
    "BackupListResponse",
    # Base schemas
    "PaginatedItems",
    # Database health schemas
    "DatabaseHealthResponse",
    "IndexStats",
    "Recommendation",
    "TableStats",
    # Event log schemas
    "EventLogCreate",
    "EventLogFilter",
    "EventLogListResponse",
    "EventLogRead",
    # Stripe schemas
    "BillingPortalResponse",
    "SubscriptionStatus",
    "WebhookResponse",
    # User schemas
    "AuthMessageResponse",
    "EmailChangeConfirm",
    "EmailVerificationConfirm",
    "PasswordResetConfirmJWT",
    "UserChangeEmail",
    "UserChangeInfo",
    "UserChangePassword",
    "UserCreate",
    "UserPasswordResetRequest",
    "UserPreviewRead",
    "UserRead",
    "UserToken",
    "UserTokenUpdate",
]
