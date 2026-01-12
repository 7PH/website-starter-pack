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

# ============================================================
# Project-specific models (add your custom schemas here)
# ============================================================
# Example:
# from .schemas.custom import MyCustomSchema, AnotherSchema
# ProjectModels = MyCustomSchema | AnotherSchema
# Models = CoreModels | ProjectModels

# If no project models, just use CoreModels
Models = CoreModels

if __name__ == "__main__":
    schema = TypeAdapter(Models).json_schema()
    print(json.dumps(schema, indent=2))
