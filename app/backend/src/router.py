# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

from fastapi import APIRouter

from .controllers import admin, auth, backups, db_health, healthcheck, stripe, users
from .router_app import router as app_router

router = APIRouter()
router.include_router(users.router, tags=["Users"])
router.include_router(auth.router, tags=["Auth"])
router.include_router(healthcheck.router, tags=["Healthcheck"])
router.include_router(stripe.router, tags=["Stripe"])
router.include_router(admin.router, tags=["Admin"])
router.include_router(backups.router, tags=["Backups"])
router.include_router(db_health.router, tags=["Database Health"])
router.include_router(app_router)
