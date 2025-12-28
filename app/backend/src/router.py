# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

from fastapi import APIRouter

from .controllers import healthcheck
from .controllers import users
from .controllers import stripe

router = APIRouter()
router.include_router(users.router, tags=["Users"])
router.include_router(healthcheck.router, tags=["Healthcheck"])
router.include_router(stripe.router, tags=["Stripe"])
