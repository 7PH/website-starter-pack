# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Pydantic schemas for the CMS editor role (CMS_ENABLED)."""

import datetime

from pydantic import BaseModel


class CmsMeRead(BaseModel):
    """CMS rights of the current user. Admins are always editors."""

    is_editor: bool


class CmsEditorRead(BaseModel):
    """A user with CMS editor rights."""

    user_id: int
    email: str | None
    created_at: datetime.datetime
