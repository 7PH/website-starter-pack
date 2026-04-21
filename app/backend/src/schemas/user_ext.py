"""
Project-specific user custom data schemas.

Sub-apps extend users by adding fields to the classes below. The values live
on the `users.custom_data` JSONB column and flow through Pydantic at both the
API boundary (validation + TS type generation) and storage time.

------------------------------------------------------------------------
UserCustomData — full data, used on UserRead / AdminUserRead
------------------------------------------------------------------------
- Surfaced in authenticated contexts (the user themselves, or an admin
  viewing them).
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

    class UserCustomData(BaseModel):
        user_type: UserType = "STUDENT"
        phone: str | None = None            # sensitive — NOT in preview
        class_id: int | None = None

    class UserPreviewCustomData(BaseModel):
        user_type: UserType = "STUDENT"     # safe to show publicly
"""

from pydantic import BaseModel


class UserCustomData(BaseModel):
    """Full custom-data shape. Add your fields here (with defaults)."""

    pass


class UserPreviewCustomData(BaseModel):
    """Preview-safe subset. Add only fields that are safe to show publicly."""

    pass
