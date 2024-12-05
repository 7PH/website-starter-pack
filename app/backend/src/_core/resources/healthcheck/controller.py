from fastapi import APIRouter, status

router = APIRouter()


@router.get("/healthcheck", response_model=str, status_code=status.HTTP_200_OK)
def healthcheck():
    return "ok"
