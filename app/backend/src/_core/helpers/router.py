from fastapi import APIRouter

from ..resources.users import controller as users

router = APIRouter()
router.include_router(users.router, tags=["Users"])
