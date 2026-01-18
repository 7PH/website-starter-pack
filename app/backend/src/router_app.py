"""
Application-specific router extensions.
This file is auto-imported by the core router if it exists.
Add your app-specific routes here.
"""

from fastapi import APIRouter

from .controllers import auth, conversations, oauth

router = APIRouter()
router.include_router(auth.router, tags=["Authentication"])
router.include_router(oauth.router, tags=["OAuth"])
router.include_router(conversations.router, tags=["Conversations"])
router.include_router(conversations.admin_router, tags=["Admin - Conversations"])
