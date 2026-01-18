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

# ============================================================
# Project-specific models (add your custom schemas here)
# ============================================================

ProjectModels = (
    ConversationCreate
    | ConversationRead
    | ConversationDetail
    | ConversationListResponse
    | ConversationUserPreview
    | MessageCreate
    | MessageRead
    | MessageListResponse
)

Models = CoreModels | ProjectModels

if __name__ == "__main__":
    schema = TypeAdapter(Models).json_schema()
    print(json.dumps(schema, indent=2))
