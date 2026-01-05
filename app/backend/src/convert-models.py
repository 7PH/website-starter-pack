"""
Generate JSON Schema from Pydantic models for frontend type generation.

Usage:
    python -m src.convert-models > ../frontend/types/models.json

Then use json-schema-to-typescript to convert to TypeScript:
    npx json2ts models.json > models.ts
"""

import json

from pydantic import TypeAdapter

from .models import (
    UserChangeInfo,
    UserChangePassword,
    UserCreate,
    UserPasswordResetRequest,
    UserPreviewRead,
    UserRead,
    UserToken,
    UserTokenUpdate,
)
from .models.admin import (
    AdminDashboardStats,
    AdminUserListResponse,
    AdminUserRead,
    AdminUserUpdate,
    ImpersonationResponse,
)
from .models.backup import (
    BackupInfo,
    BackupListResponse,
)
from .models.db_health import (
    DatabaseHealthResponse,
    IndexStats,
    Recommendation,
    TableStats,
)
from .models.event_log import (
    EventLogFilter,
    EventLogListResponse,
    EventLogRead,
)

# Union of all models to export to frontend
Models = (
    # User models
    UserRead
    | UserPreviewRead
    | UserCreate
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
    # Database health models
    | DatabaseHealthResponse
    | TableStats
    | IndexStats
    | Recommendation
)

if __name__ == "__main__":
    schema = TypeAdapter(Models).json_schema()
    print(json.dumps(schema, indent=2))
