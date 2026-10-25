# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""CMS photo library (CMS_ENABLED): upload, list, edit and delete photos. Editors and admins only."""

import secrets

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..helpers.cms_auth import get_current_cms_editor
from ..helpers.cms_media import (
    MAX_UPLOAD_BYTES,
    delete_media_files,
    media_dir,
    media_to_read,
    pages_using_media,
    process_image,
    safe_original_name,
    write_media_files,
)
from ..helpers.db import get_session
from ..helpers.logging import get_logger
from ..models.cms import CmsMediaBase
from ..schemas.cms_media import CmsMediaListResponse, CmsMediaRead, CmsMediaUpdate
from ..schemas.user import UserRead

router = APIRouter(prefix="/cms", dependencies=[Depends(get_current_cms_editor)])
logger = get_logger(__name__)


def _get_media_or_404(session: Session, media_id: int) -> CmsMediaBase:
    media = session.get(CmsMediaBase, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Photo not found")
    return media


@router.get("/media", response_model=CmsMediaListResponse)
def list_media(
    *,
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(60, ge=1, le=200),
):
    query = session.query(CmsMediaBase)
    total = query.count()
    rows = query.order_by(CmsMediaBase.id.desc()).offset(offset).limit(limit).all()
    return CmsMediaListResponse(items=[media_to_read(m) for m in rows], total=total)


# Plain def: Pillow work is CPU-bound and FastAPI runs sync endpoints in a thread pool.
@router.post("/media", response_model=CmsMediaRead, status_code=status.HTTP_201_CREATED)
def upload_media(
    *,
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_current_cms_editor),
    file: UploadFile = File(...),
    alt: str = Form("", max_length=300),
):
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


@router.get("/media/{media_id}", response_model=CmsMediaRead)
def get_media(media_id: int, session: Session = Depends(get_session)):
    return media_to_read(_get_media_or_404(session, media_id))


@router.patch("/media/{media_id}", response_model=CmsMediaRead)
def update_media(media_id: int, payload: CmsMediaUpdate, session: Session = Depends(get_session)):
    media = _get_media_or_404(session, media_id)
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(media, key, value.strip() if isinstance(value, str) else value)
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
