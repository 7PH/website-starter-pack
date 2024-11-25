from fastapi import APIRouter

from .controller import hello_world, users

router = APIRouter()
router.include_router(users.router, tags=["Users"])
router.include_router(hello_world.router, tags=["Hello World"])
