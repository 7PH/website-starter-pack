# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

from fastapi import APIRouter

from .controllers import healthcheck, stripe, users
from .router_app import router as app_router

router = APIRouter()
router.include_router(users.router, tags=["Users"])
router.include_router(healthcheck.router, tags=["Healthcheck"])
router.include_router(stripe.router, tags=["Stripe"])
router.include_router(app_router)
