from fastapi import APIRouter
from src.core.resources.users import controller as users

from .controller import hello_world

router = APIRouter()
router.include_router(users.router, tags=["Users"])
router.include_router(hello_world.router, tags=["Hello World"])
