"""
Project-specific user custom data schemas.

Sub-apps extend users by adding fields to the classes below. The values live
on the `users.custom_data` JSONB column and flow through Pydantic at both the
API boundary (validation + TS type generation) and storage time.

------------------------------------------------------------------------
UserCustomDataWritable — fields a user may set on THEMSELVES
------------------------------------------------------------------------
- Used on the user-controlled write paths: signup (POST /users) and the
  /account profile edit (update_me).
- Put a field here ONLY if a user is allowed to set it on their own account.
- PRIVILEGE ESCALATION GUARD: privileged fields (roles, entitlements,
  credits, internal flags, ...) must NOT live here. Declare those on
  UserCustomData instead — then only admins (who write the full type) can
  set them. If a privileged field were writable, a user could grant it to
  themselves by POSTing it in their own create/update payload.

------------------------------------------------------------------------
UserCustomData — full data, used on UserRead / AdminUserRead + admin writes
------------------------------------------------------------------------
- Surfaced in authenticated contexts (the user themselves, or an admin
  viewing them), and is the type admins write through (update_user_by_admin).
- Inherits UserCustomDataWritable, so every self-writable field is part of
  the full shape. Add privileged/admin-only fields directly on this class.
- ALL FIELDS MUST HAVE DEFAULTS. Reasons:
    1. Create/update pipelines validate partial payloads — a required field
       would reject partial updates.
    2. Pre-existing user rows have `custom_data={}`; a required field would
       break reads of older rows.
    3. The `Field(default_factory=UserCustomData)` pattern on UserRead needs
       the class to be constructible with no arguments.
- Wire the inputs into `components/users/MetadataFields.vue` (appears in the
  /account profile form and the admin user edit form).

------------------------------------------------------------------------
UserPreviewCustomData — preview-safe subset, used on UserPreviewRead
------------------------------------------------------------------------
- Surfaced in public/semi-public contexts (invitation previews, message
  author snippets, ...).
- Pydantic filters `user.custom_data` through this class at serialization
  time, so any key you do NOT declare here is DROPPED before reaching the
  wire. Omit anything sensitive (phone, address, internal notes, ...).
- All fields must have defaults (same reasons as UserCustomData).

------------------------------------------------------------------------
Signup flow
------------------------------------------------------------------------
There's no separate "signup" schema. To require a field at the web signup
form, declare it in UserCustomData (with a default for storage), then render
it in `components/users/SignupMetadataFields.vue` and enforce required-ness
in that component's validate() method. Enforcement is UI-only: OAuth signups
and direct POSTs to `/users` bypass the form and get the declared defaults.

------------------------------------------------------------------------
Example — school app
------------------------------------------------------------------------
    from typing import Literal

    UserType = Literal["STUDENT", "TEACHER", "PARENT"]

    class UserCustomDataWritable(BaseModel):
        phone: str | None = None            # user may edit their own phone

    class UserCustomData(UserCustomDataWritable):
        # user_type is privileged: a student must not make themselves a
        # teacher, so it lives here (admin-writable) and NOT in Writable.
        user_type: UserType = "STUDENT"
        class_id: int | None = None

    class UserPreviewCustomData(BaseModel):
        user_type: UserType = "STUDENT"     # safe to show publicly
"""

from pydantic import BaseModel


class UserCustomDataWritable(BaseModel):
    """Fields a user may set on THEMSELVES (signup + /account profile edit).

    Add ONLY self-writable fields here. Privileged fields (roles,
    entitlements, credits, internal flags, ...) must NOT go here — declare
    them on UserCustomData so only admins can write them. All fields must
    have defaults (same reasons as UserCustomData)."""

    pass


class UserCustomData(UserCustomDataWritable):
    """Full custom-data shape, used on reads and the admin write path.

    Inherits every self-writable field; declare privileged/admin-only fields
    directly here. Add your fields with defaults."""

    pass


class UserPreviewCustomData(BaseModel):
    """Preview-safe subset. Add only fields that are safe to show publicly."""

    pass
