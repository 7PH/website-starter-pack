"""
Generate JSON Schema from Pydantic models for frontend type generation.

Usage:
    python -m src.convert-models > ../frontend/types/models.json

Then use json-schema-to-typescript to convert to TypeScript:
    npx json2ts models.json > models.ts
"""

import json

from pydantic import TypeAdapter

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
from .schemas.stripe import (
    BillingPortalResponse,
    SubscriptionStatus,
)

# Union of all models to export to frontend
Models = (
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
)

if __name__ == "__main__":
    schema = TypeAdapter(Models).json_schema()
    print(json.dumps(schema, indent=2))
