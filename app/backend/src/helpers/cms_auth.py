# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Access checks for CMS editing (CMS_ENABLED). Admins can always edit."""

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from ..models.cms import CmsEditorBase
from ..schemas.user import UserRead
from .auth import get_current_user
from .db import get_session


def is_cms_editor(session: Session, user_id: int) -> bool:
    """True when the user is an admin or in cms_editors. Read from the DB, never from the JWT."""
    from ..crud.users import get_user_by_id

    db_user = get_user_by_id(session, user_id)
    if not db_user:
        return False
    if db_user.is_admin:
        return True
    return session.get(CmsEditorBase, user_id) is not None


async def get_current_cms_editor(
    current_user: UserRead = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> UserRead:
    """Current user, requiring CMS edit rights (admin or editor). 403 otherwise."""
    if not is_cms_editor(session, current_user.id):
        raise HTTPException(status_code=403, detail="CMS editor access required")
    return current_user
