# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""CMS photo library (CMS_ENABLED): upload, list, edit and delete photos. Editors and admins only."""

import secrets
from datetime import UTC, datetime
from enum import StrEnum

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Query as SqlQuery
from sqlalchemy.orm import Session

from ..helpers.cms_auth import get_current_cms_editor
from ..helpers.cms_media import (
    MAX_UPLOAD_BYTES,
    delete_media_files,
    media_dir,
    media_to_read,
    media_usage,
    pages_using_media,
    process_image,
    safe_original_name,
    write_media_files,
)
from ..helpers.db import get_session
from ..helpers.logging import get_logger
from ..models.cms import CmsMediaBase
from ..schemas.cms_media import (
    CmsMediaBulkDelete,
    CmsMediaBulkDeleteResponse,
    CmsMediaBulkUpdate,
    CmsMediaDetail,
    CmsMediaLibraryItem,
    CmsMediaListResponse,
    CmsMediaRead,
    CmsMediaUpdate,
)
from ..schemas.user import UserRead

router = APIRouter(prefix="/cms", dependencies=[Depends(get_current_cms_editor)])
logger = get_logger(__name__)


def _get_media_or_404(session: Session, media_id: int) -> CmsMediaBase:
    media = session.get(CmsMediaBase, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Photo not found")
    return media


class MediaSort(StrEnum):
    newest = "newest"
    oldest = "oldest"
    name = "name"
    # Photos shown on a page first, then newest.
    used = "used"


class MediaUsageFilter(StrEnum):
    used = "used"
    unused = "unused"
    # Shown on a page but without a description.
    missing_alt = "missing_alt"


class MediaFilters:
    """Library filters, shared by the list and the id list behind "select all"."""

    def __init__(
        self,
        q: str = Query("", max_length=100),
        usage: MediaUsageFilter | None = None,
        # "" for photos in no folder.
        folder: str | None = Query(None, max_length=100),
    ):
        self.q = q.strip()
        self.usage = usage
        self.folder = folder

    def apply(self, query: SqlQuery, used_ids: set[int]) -> SqlQuery:
        if self.q:
            query = query.filter(
                or_(
                    CmsMediaBase.original_name.icontains(self.q, autoescape=True),
                    CmsMediaBase.alt.icontains(self.q, autoescape=True),
                )
            )
        if self.folder is not None:
            query = query.filter(CmsMediaBase.folder == self.folder if self.folder else CmsMediaBase.folder.is_(None))
        if self.usage == MediaUsageFilter.used:
            query = query.filter(CmsMediaBase.id.in_(used_ids))
        elif self.usage == MediaUsageFilter.unused:
            query = query.filter(CmsMediaBase.id.not_in(used_ids))
        elif self.usage == MediaUsageFilter.missing_alt:
            query = query.filter(CmsMediaBase.id.in_(used_ids), CmsMediaBase.alt == "")
        return query


def _order(sort: MediaSort, used_ids: set[int]) -> list:
    # id last: rows with the same date or name must keep one order across pages.
    if sort == MediaSort.oldest:
        return [CmsMediaBase.created_at.asc(), CmsMediaBase.id.asc()]
    if sort == MediaSort.name:
        return [func.lower(CmsMediaBase.original_name).asc(), CmsMediaBase.id.asc()]
    newest = [CmsMediaBase.created_at.desc(), CmsMediaBase.id.desc()]
    if sort == MediaSort.used and used_ids:
        return [case((CmsMediaBase.id.in_(used_ids), 0), else_=1), *newest]
    return newest


@router.get("/media", response_model=CmsMediaListResponse)
def list_media(
    *,
    session: Session = Depends(get_session),
    filters: MediaFilters = Depends(),
    sort: MediaSort = MediaSort.newest,
    offset: int = Query(0, ge=0),
    limit: int = Query(60, ge=1, le=200),
):
    usage = media_usage(session)
    used_ids = set(usage)
    query = filters.apply(session.query(CmsMediaBase), used_ids)
    rows = query.order_by(*_order(sort, used_ids)).offset(offset).limit(limit).all()
    missing_alt = (
        session.query(func.count(CmsMediaBase.id))
        .filter(CmsMediaBase.id.in_(used_ids), CmsMediaBase.alt == "")
        .scalar()
    )
    folders = session.query(CmsMediaBase.folder).filter(CmsMediaBase.folder.isnot(None)).distinct().all()
    return CmsMediaListResponse(
        items=[
            CmsMediaLibraryItem(**media_to_read(m).model_dump(), usage_count=len(usage.get(m.id, []))) for m in rows
        ],
        total=query.count(),
        missing_alt=missing_alt,
        folders=sorted(f for (f,) in folders),
    )


@router.get("/media/ids", response_model=list[int])
def list_media_ids(*, session: Session = Depends(get_session), filters: MediaFilters = Depends()):
    """Every id matching the filters, for "select all" without loading every photo."""
    used_ids = set(media_usage(session))
    return [i for (i,) in filters.apply(session.query(CmsMediaBase.id), used_ids).all()]


@router.post("/media/bulk-delete", response_model=CmsMediaBulkDeleteResponse)
def bulk_delete_media(payload: CmsMediaBulkDelete, session: Session = Depends(get_session)):
    """Deletes the given photos, except those still shown on a page."""
    used_ids = set(media_usage(session))
    rows = session.query(CmsMediaBase).filter(CmsMediaBase.id.in_(payload.ids)).all()
    doomed = [m for m in rows if m.id not in used_ids]
    folders = [media_dir(m) for m in doomed]
    for media in doomed:
        session.delete(media)
    session.commit()
    # Files go after the commit: a failed commit must not leave rows pointing at nothing.
    for folder in folders:
        delete_media_files(folder)
    return CmsMediaBulkDeleteResponse(deleted=[m.id for m in doomed], in_use=[m.id for m in rows if m.id in used_ids])


@router.post("/media/bulk-update", status_code=status.HTTP_204_NO_CONTENT)
def bulk_update_media(payload: CmsMediaBulkUpdate, session: Session = Depends(get_session)):
    session.query(CmsMediaBase).filter(CmsMediaBase.id.in_(payload.ids)).update(
        {CmsMediaBase.folder: payload.folder.strip() or None}, synchronize_session=False
    )
    session.commit()


# Plain def: Pillow work is CPU-bound and FastAPI runs sync endpoints in a thread pool.
@router.post("/media", response_model=CmsMediaRead, status_code=status.HTTP_201_CREATED)
def upload_media(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_current_cms_editor),
    file: UploadFile = File(...),
    alt: str = Form("", max_length=300),
    # Original date of an imported photo, so it sorts by when it was taken or first published.
    created_at: datetime | None = Form(None),
):
    if created_at and created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    if created_at and created_at > datetime.now(UTC):
        raise HTTPException(status_code=422, detail="Date is in the future")
    # One byte past the limit is enough to detect an oversized upload without loading it all in memory.
    width, height, files = process_image(file.file.read(MAX_UPLOAD_BYTES + 1))

    media = CmsMediaBase(
        token=secrets.token_urlsafe(9),
        original_name=safe_original_name(file.filename),
        alt=alt.strip(),
        width=width,
        height=height,
        sizes=sorted(files),
        uploaded_by=user.id,
        created_at=created_at,
    )
    session.add(media)
    session.flush()
    folder = media_dir(media)
    try:
        write_media_files(folder, files)
        session.commit()
    except Exception:
        session.rollback()
        delete_media_files(folder)
        raise
    session.refresh(media)
    logger.info(f"CMS media {media.id} uploaded by user {user.id} ({width}x{height})")
    return media_to_read(media)


@router.get("/media/{media_id}", response_model=CmsMediaDetail)
def get_media(media_id: int, session: Session = Depends(get_session)):
    media = _get_media_or_404(session, media_id)
    return CmsMediaDetail(**media_to_read(media).model_dump(), used_by=pages_using_media(session, media_id))


@router.patch("/media/{media_id}", response_model=CmsMediaRead)
def update_media(media_id: int, payload: CmsMediaUpdate, session: Session = Depends(get_session)):
    media = _get_media_or_404(session, media_id)
    for key, value in payload.model_dump(exclude_none=True).items():
        if isinstance(value, str):
            value = value.strip()
        # An empty folder means no folder.
        setattr(media, key, None if key == "folder" and not value else value)
    session.commit()
    session.refresh(media)
    return media_to_read(media)


@router.delete("/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(media_id: int, session: Session = Depends(get_session)):
    """409 when a page still shows the photo, body `{"detail": str, "pages": [CmsMediaUsage]}`."""
    media = _get_media_or_404(session, media_id)
    pages = pages_using_media(session, media_id)
    if pages:
        # Returned, not raised: the app's HTTPException handler turns any detail into a string.
        return JSONResponse(
            status_code=409,
            content={"detail": "Photo is used by pages", "pages": [p.model_dump() for p in pages]},
        )
    folder = media_dir(media)
    session.delete(media)
    session.commit()
    # Files go after the commit: a failed commit must not leave a row pointing at nothing.
    delete_media_files(folder)
