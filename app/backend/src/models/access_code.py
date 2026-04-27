# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Access-code SQLAlchemy model. Maps a code to a user for sign-in by code.

The ``user_id`` FK points to the **managed account itself** (the leaf user
with ``auth_method='access_code'``), NOT to the manager/owner. The owner of
the managed account lives on ``managed_account_groups.owner_id`` — a separate
hierarchy. The code authenticates the managed account directly.

PK is the composite ``(user_id, code)``. Codes are unique *within a single
managed account* (which only has one active code at a time anyway), so two
unrelated managers can each have a student whose code happens to be the same
string. Sign-in lookups always pass both halves, so this is safe.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, PrimaryKeyConstraint, String, func

from ..helpers.db import Base


class AccessCodeBase(Base):
    __tablename__ = "access_codes"

    code = Column(String(64), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True, default=None)
    expires_at = Column(DateTime(timezone=True), nullable=True, default=None)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (PrimaryKeyConstraint("user_id", "code", name="access_codes_pkey"),)
