from fastapi import APIRouter
from src._core.resources.users import controller as users

router = APIRouter()
router.include_router(users.router, tags=["Users"])
