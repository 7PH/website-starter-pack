"""
Application-specific router extensions.
This file is auto-imported by the core router if it exists.
Add your app-specific routes here.
"""

from fastapi import APIRouter

from .controllers import auth, oauth

router = APIRouter()
router.include_router(auth.router, tags=["Authentication"])
router.include_router(oauth.router, tags=["OAuth"])
