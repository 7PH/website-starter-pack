# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
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
    UserLogin,
    UserPasswordResetConfirm,
    UserPasswordResetRequest,
    UserPreviewRead,
    UserRead,
    UserToken,
    UserTokenUpdate,
)

# Union of all models to export to frontend
Models = (
    UserRead
    | UserPreviewRead
    | UserCreate
    | UserLogin
    | UserChangeInfo
    | UserChangePassword
    | UserToken
    | UserTokenUpdate
    | UserPasswordResetRequest
    | UserPasswordResetConfirm
)

if __name__ == "__main__":
    schema = TypeAdapter(Models).json_schema()
    print(json.dumps(schema, indent=2))
