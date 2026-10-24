# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""CMS pages (CMS_ENABLED): public reads, and editing for admins and editors."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from ..helpers.cms_auth import get_current_cms_editor
from ..helpers.cms_pages import apply_update, new_fixed_page, page_to_read, pages_to_summaries, save_page, unique_slug
from ..helpers.cms_templates import get_templates
from ..helpers.db import get_session
from ..models.cms import CmsPageBase
from ..schemas.cms_page import (
    CmsAdminPagesResponse,
    CmsFixedPageItem,
    CmsPageAdminRead,
    CmsPageCreate,
    CmsPageListItem,
    CmsPageRead,
    CmsPageUpdate,
    CmsPostListResponse,
    CmsSitemapEntry,
    CmsTemplateField,
    CmsTemplateRead,
)
from ..schemas.user import UserRead

router = APIRouter(prefix="/cms")


def _published_pages(session: Session):
    return session.query(CmsPageBase).filter(CmsPageBase.slug.isnot(None), CmsPageBase.published.is_(True))


def _fixed_page(session: Session, key: str) -> CmsPageBase:
    """Stored row of a fixed page, or an unsaved one with its defaults. 404 if the key is not a fixed template."""
    template = get_templates().get(key)
    if not template or not template.fixed:
        raise HTTPException(status_code=404, detail="Page not found")
    return session.query(CmsPageBase).filter(CmsPageBase.fixed_key == key).first() or new_fixed_page(key)


def _free_page_or_404(session: Session, page_id: int) -> CmsPageBase:
    page = session.get(CmsPageBase, page_id)
    if not page or page.slug is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


def _save(session: Session, page: CmsPageBase, data: CmsPageUpdate) -> CmsPageAdminRead:
    save_page(session, page, data)
    return page_to_read(session, page, admin=True)


# ============================================================================
# Public
# ============================================================================


@router.get("/pages/by-slug/{slug}", response_model=CmsPageRead)
def get_page_by_slug(slug: str, session: Session = Depends(get_session)):
    """A published free page. Drafts are 404 here, editors preview them via the admin endpoints."""
    page = _published_pages(session).filter(CmsPageBase.slug == slug).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page_to_read(session, page)


@router.get("/fixed/{key}", response_model=CmsPageRead)
def get_fixed_page(key: str, session: Session = Depends(get_session)):
    """A fixed page with defaults merged. Never writes: an unedited page is served from its defaults."""
    return page_to_read(session, _fixed_page(session, key))


@router.get("/posts", response_model=CmsPostListResponse)
def list_posts(
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
):
    """Published pages shown in the blog, newest first."""
    query = _published_pages(session).filter(CmsPageBase.show_in_blog.is_(True))
    pages = query.order_by(CmsPageBase.published_at.desc(), CmsPageBase.id.desc()).offset(offset).limit(limit).all()
    return CmsPostListResponse(items=pages_to_summaries(session, pages), total=query.count())


@router.get("/sitemap", response_model=list[CmsSitemapEntry])
def get_sitemap(session: Session = Depends(get_session)):
    """Published free pages, consumed by the frontend sitemap at request time."""
    rows = _published_pages(session).with_entities(CmsPageBase.slug, CmsPageBase.updated_at).all()
    return [CmsSitemapEntry(loc=f"/{slug}", lastmod=updated_at) for slug, updated_at in rows]


# ============================================================================
# Editors
# ============================================================================


@router.get("/templates", response_model=list[CmsTemplateRead])
def list_templates(editor: UserRead = Depends(get_current_cms_editor)):
    return [
        CmsTemplateRead(
            name=name,
            label=template.label,
            fixed=template.fixed,
            fields=[CmsTemplateField(name=field_name, **vars(field)) for field_name, field in template.fields.items()],
        )
        for name, template in get_templates().items()
    ]


@router.get("/admin/pages", response_model=CmsAdminPagesResponse)
def list_pages(session: Session = Depends(get_session), editor: UserRead = Depends(get_current_cms_editor)):
    """Fixed pages (one per fixed template, saved or not) then free pages, last edited first."""
    saved = dict(
        session.query(CmsPageBase.fixed_key, CmsPageBase.updated_at).filter(CmsPageBase.fixed_key.isnot(None)).all()
    )
    fixed = [CmsFixedPageItem(key=key, updated_at=saved.get(key)) for key, t in get_templates().items() if t.fixed]
    pages = session.query(CmsPageBase).filter(CmsPageBase.slug.isnot(None)).order_by(CmsPageBase.updated_at.desc())
    return CmsAdminPagesResponse(
        fixed=fixed, pages=[CmsPageListItem.model_validate(p, from_attributes=True) for p in pages]
    )


@router.post("/admin/pages", response_model=CmsPageAdminRead, status_code=status.HTTP_201_CREATED)
def create_page(
    data: CmsPageCreate,
    session: Session = Depends(get_session),
    editor: UserRead = Depends(get_current_cms_editor),
):
    template = get_templates().get(data.template)
    if not template or template.fixed:
        raise HTTPException(status_code=422, detail="Unknown page template")
    page = CmsPageBase(template=data.template, slug=unique_slug(session, data.title), title="", fields={})
    return _save(session, page, CmsPageUpdate(title=data.title))


@router.get("/admin/pages/{page_id}", response_model=CmsPageAdminRead)
def get_page(page_id: int, session: Session = Depends(get_session), editor: UserRead = Depends(get_current_cms_editor)):
    return page_to_read(session, _free_page_or_404(session, page_id), admin=True)


@router.patch("/admin/pages/{page_id}", response_model=CmsPageAdminRead)
def update_page(
    page_id: int,
    data: CmsPageUpdate,
    session: Session = Depends(get_session),
    editor: UserRead = Depends(get_current_cms_editor),
):
    return _save(session, _free_page_or_404(session, page_id), data)


@router.post("/admin/pages/{page_id}/preview", response_model=CmsPageAdminRead)
def preview_page(
    page_id: int,
    data: CmsPageUpdate,
    session: Session = Depends(get_session),
    editor: UserRead = Depends(get_current_cms_editor),
):
    """The page with unsaved changes applied, validated and sanitized like a save, then discarded."""
    page = _free_page_or_404(session, page_id)
    apply_update(session, page, data)
    read = page_to_read(session, page, admin=True)
    session.rollback()
    return read


@router.delete("/admin/pages/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_page(
    page_id: int, session: Session = Depends(get_session), editor: UserRead = Depends(get_current_cms_editor)
):
    session.delete(_free_page_or_404(session, page_id))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/admin/fixed/{key}", response_model=CmsPageAdminRead)
def get_fixed_page_admin(
    key: str, session: Session = Depends(get_session), editor: UserRead = Depends(get_current_cms_editor)
):
    return page_to_read(session, _fixed_page(session, key), admin=True)


@router.patch("/admin/fixed/{key}", response_model=CmsPageAdminRead)
def update_fixed_page(
    key: str,
    data: CmsPageUpdate,
    session: Session = Depends(get_session),
    editor: UserRead = Depends(get_current_cms_editor),
):
    """Creates the row on first save."""
    return _save(session, _fixed_page(session, key), data)
