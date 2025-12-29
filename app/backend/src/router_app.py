"""
Application-specific router extensions.
This file is auto-imported by the core router if it exists.
Add your app-specific routes here.
"""

from fastapi import APIRouter

from .controllers import auth

router = APIRouter()
router.include_router(auth.router, tags=["Authentication"])
