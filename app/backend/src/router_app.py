"""
Application-specific router extensions.
This file is auto-imported by the core router if it exists.
Add your app-specific routes here.
"""

from fastapi import APIRouter

from .constants import LLM_ENABLED
from .controllers import auth, conversations, oauth
from .helpers.oauth import OAUTH_ENABLED

router = APIRouter()
router.include_router(auth.router, tags=["Authentication"])
# These two stay registered when their flag is off (the handlers reject), so the
# schema has to follow the flag by hand.
router.include_router(oauth.router, tags=["OAuth"], include_in_schema=OAUTH_ENABLED)
router.include_router(conversations.router, tags=["Conversations"], include_in_schema=LLM_ENABLED)
router.include_router(conversations.admin_router, tags=["Admin - Conversations"], include_in_schema=False)
