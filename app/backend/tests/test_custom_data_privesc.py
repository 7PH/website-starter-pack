# ⚠️ STARTERPACK CORE — DO NOT MODIFY
"""Guards against privilege escalation through user.custom_data.

User-controlled write schemas (signup + profile edit) must accept only the
writable subset, so a sub-app field declared on UserCustomData but not on
UserCustomDataWritable can never be self-set. Admin writes keep the full type.
"""

import os
from typing import get_args

# Importing src pulls in helpers.db which reads APP_DB_* at module load.
os.environ.setdefault("APP_DB_USER", "test")
os.environ.setdefault("APP_DB_PASSWORD", "test")
os.environ.setdefault("APP_DB_NAME", "test")

from src.schemas.admin import AdminUserUpdate
from src.schemas.user import UserChangeInfo, UserCreate
from src.schemas.user_ext import UserCustomData, UserCustomDataWritable


def _custom_data_type(model):
    """The non-None type annotating a schema's custom_data field."""
    annotation = model.model_fields["custom_data"].annotation
    args = [a for a in get_args(annotation) if a is not type(None)]
    return args[0] if args else annotation


def test_full_type_extends_writable():
    # Single source of truth: every self-writable field is part of the full
    # shape, and privileged fields added to the full type are the only extras.
    assert issubclass(UserCustomData, UserCustomDataWritable)


def test_self_write_schemas_use_writable_subset():
    # The privesc boundary: users write through the restricted type.
    assert _custom_data_type(UserCreate) is UserCustomDataWritable
    assert _custom_data_type(UserChangeInfo) is UserCustomDataWritable


def test_admin_write_keeps_full_type():
    # Admins must still be able to set every field, including privileged ones.
    assert _custom_data_type(AdminUserUpdate) is UserCustomData


def test_undeclared_field_is_dropped_on_self_write():
    # A user POSTing an undeclared key (e.g. a privileged field they don't
    # own) must have it stripped at the Pydantic boundary, not persisted.
    payload = {"first_name": "Ann", "last_name": "Lee", "custom_data": {"is_admin": True}}
    parsed = UserChangeInfo(**payload)
    assert parsed.custom_data is not None
    assert parsed.custom_data.model_dump() == {}
