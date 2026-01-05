# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..helpers.db import get_session

router = APIRouter()


class HealthCheckResponse(BaseModel):
    status: str
    database: str


@router.get("/healthcheck", response_model=HealthCheckResponse, status_code=status.HTTP_200_OK)
def healthcheck(session: Session = Depends(get_session)):
    """Health check endpoint that verifies database connectivity."""
    db_status = "ok"
    try:
        session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return HealthCheckResponse(
        status="ok",
        database=db_status,
    )
