# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Pydantic schemas for database backup operations."""

from datetime import datetime

from pydantic import BaseModel


class BackupInfo(BaseModel):
    """Information about a single backup file."""

    filename: str
    size: int  # bytes
    created_at: datetime


class BackupListResponse(BaseModel):
    """Response for backup list endpoint."""

    items: list[BackupInfo]
    total: int
