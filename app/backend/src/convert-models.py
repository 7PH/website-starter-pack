"""
Generate JSON Schema from Pydantic models for frontend type generation.

Usage:
    python -m src.convert-models > ../frontend/types/models.json

Then use json-schema-to-typescript to convert to TypeScript:
    npx json2ts models.json > models.ts
"""

import json

from pydantic import TypeAdapter

from .convert_models_core import CoreModels
from .schemas.config_ext import BackendConfig
from .schemas.conversation import (
    ConversationCreate,
    ConversationDetail,
    ConversationListResponse,
    ConversationRead,
    ConversationUserPreview,
    MessageCreate,
    MessageListResponse,
    MessageRead,
)
from .schemas.organization_ext import OrganizationCustomData
from .schemas.user_ext import UserCustomData, UserPreviewCustomData

# ============================================================
# Project-specific models (add your custom schemas here)
# ============================================================

ProjectModels = (
    BackendConfig
    | ConversationCreate
    | ConversationRead
    | ConversationDetail
    | ConversationListResponse
    | ConversationUserPreview
    | MessageCreate
    | MessageRead
    | MessageListResponse
    | OrganizationCustomData
    | UserCustomData
    | UserPreviewCustomData
)

Models = CoreModels | ProjectModels

if __name__ == "__main__":
    schema = TypeAdapter(Models).json_schema()
    print(json.dumps(schema, indent=2))
