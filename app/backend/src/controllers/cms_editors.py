# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""CMS editor role (CMS_ENABLED): who may edit pages and photos without being admin."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..constants import EventType
from ..crud.event_logs import log_event
from ..helpers.auth import get_current_admin, get_current_user, get_user_or_404
from ..helpers.cms_auth import is_cms_editor
from ..helpers.db import get_session
from ..models.cms import CmsEditorBase
from ..models.user import UserBase
from ..schemas.cms_editor import CmsEditorRead, CmsMeRead
from ..schemas.user import UserRead

router = APIRouter(prefix="/cms")


def _commit_change(session: Session, request: Request, user_id: int, is_editor: bool) -> None:
    """Commit the pending editor change and log it."""
    session.commit()
    log_event(
        session,
        action=EventType.ADMIN_USER_UPDATE,
        user_id=user_id,
        details={"changes": {"cms_editor": {"from": not is_editor, "to": is_editor}}},
        request=request,
    )


@router.get("/me", response_model=CmsMeRead)
def get_cms_me(
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_current_user),
):
    """Whether the current user may edit CMS content."""
    return CmsMeRead(is_editor=is_cms_editor(session, user.id))


@router.get("/editors", response_model=list[CmsEditorRead])
def list_cms_editors(
    session: Session = Depends(get_session),
    admin: UserRead = Depends(get_current_admin),
):
    """List users with editor rights (admins are editors implicitly and not listed)."""
    rows = session.execute(
        select(CmsEditorBase.user_id, UserBase.email, CmsEditorBase.created_at)
        .join(UserBase, UserBase.id == CmsEditorBase.user_id)
        .where(UserBase.deleted_at.is_(None))
        .order_by(CmsEditorBase.created_at)
    ).all()
    return [CmsEditorRead(user_id=r.user_id, email=r.email, created_at=r.created_at) for r in rows]


@router.put("/editors/{user_id}", response_model=CmsEditorRead)
def add_cms_editor(
    user_id: int,
    request: Request,
    session: Session = Depends(get_session),
    admin: UserRead = Depends(get_current_admin),
):
    """Give a user editor rights. Idempotent."""
    user = get_user_or_404(session, user_id)
    editor = session.get(CmsEditorBase, user_id)
    if editor is None:
        editor = CmsEditorBase(user_id=user_id)
        session.add(editor)
        _commit_change(session, request, user_id, is_editor=True)
    return CmsEditorRead(user_id=user_id, email=user.email, created_at=editor.created_at)


@router.delete("/editors/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_cms_editor(
    user_id: int,
    request: Request,
    session: Session = Depends(get_session),
    admin: UserRead = Depends(get_current_admin),
):
    """Remove a user's editor rights. Idempotent."""
    editor = session.get(CmsEditorBase, user_id)
    if editor is not None:
        session.delete(editor)
        _commit_change(session, request, user_id, is_editor=False)
