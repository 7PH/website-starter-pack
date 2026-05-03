# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Pydantic schemas for managed account groups and the accounts inside them."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ManagedAccountGroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ManagedAccountGroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    archived: bool | None = None


class ManagedAccountGroupRead(BaseModel):
    """A group as seen by its owner."""

    id: int
    owner_id: int
    name: str
    share_token: str
    created_at: datetime
    archived_at: datetime | None
    member_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ManagedAccountCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=255)


class ManagedAccountUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    # Move the account to a different group owned by the same user.
    managed_account_group_id: int | None = Field(default=None, gt=0)


class ManagedAccountRead(BaseModel):
    """A managed account as seen by its group's owner. Includes the active code."""

    id: int
    display_name: str | None
    managed_account_group_id: int | None
    # Nullable: legacy users.created_at can be NULL in older rows.
    created_at: datetime | None = None
    code: str | None = None  # active code, populated by the controller

    model_config = ConfigDict(from_attributes=True)


class ManagedAccountCreated(BaseModel):
    """Response shape for create-account: includes the freshly minted code."""

    account: ManagedAccountRead
    code: str


class ManagedAccountBulkCreate(BaseModel):
    """Bulk-create payload. Each entry is a single display_name string; the
    client does the parsing/normalization (delimiter detection, last-name-first
    swap, etc.) before posting."""

    accounts: list[ManagedAccountCreate] = Field(min_length=1, max_length=200)


class ManagedAccountBulkCreated(BaseModel):
    """Response: created accounts (with codes populated) + count of duplicates
    silently skipped (in-batch dups + ones that already existed in the group)."""

    accounts: list[ManagedAccountRead]
    skipped: int = 0


class PublicPickerEntry(BaseModel):
    """One name in the public picker list."""

    managed_account_id: int
    display_name: str | None


class PublicPickerPayload(BaseModel):
    """Anonymous response from GET /c/:share_token. No owner data leaks here."""

    group_name: str
    members: list[PublicPickerEntry]
