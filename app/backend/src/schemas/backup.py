# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Pydantic schemas for database backup operations."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class BackupTag(str, Enum):
    """Encodes the reason a backup was created. Values are lowercase, used in filenames."""

    automatic = "automatic"
    manual = "manual"
    prerestore = "prerestore"


class BackupInfo(BaseModel):
    """Information about a single backup file."""

    filename: str
    size: int  # bytes
    created_at: datetime
    comment: str | None = Field(default=None, json_schema_extra={"title": "BackupComment"})


class BackupListResponse(BaseModel):
    """Response for backup list endpoint."""

    items: list[BackupInfo]
    total: int


class RestoreRequest(BaseModel):
    """Request body for restore endpoint. confirm_filename must match the URL filename."""

    confirm_filename: str
