from fastapi import APIRouter

from .healthcheck import controller as healthcheck
from .users import controller as users

router = APIRouter()
router.include_router(users.router, tags=["Users"])
router.include_router(healthcheck.router, tags=["Healthcheck"])
