from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_session

router = APIRouter()


@router.get("/hello-world", response_model=str)
def get_account(*, session: Session = Depends(get_session)) -> str:
    return "Hello World!!!"
