# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

from fastapi import APIRouter

from .constants import MANAGED_ACCOUNTS_ENABLED, ORG_INVITATIONS_ENABLED, ORGANIZATIONS_ENABLED, STRIPE_ENABLED
from .controllers import (
    admin,
    auth,
    backups,
    db_health,
    healthcheck,
    invitations,
    managed_account_groups,
    organizations,
    stripe,
    users,
)
from .router_app import router as app_router

# Unversioned routes (healthcheck for load balancers/infrastructure)
router_unversioned = APIRouter()
router_unversioned.include_router(healthcheck.router, tags=["Healthcheck"])

# V1 API routes
router_v1 = APIRouter(prefix="/v1")
router_v1.include_router(healthcheck.router, tags=["Healthcheck"])  # Also available versioned for frontend
router_v1.include_router(users.router, tags=["Users"])
router_v1.include_router(auth.router, tags=["Auth"])
if STRIPE_ENABLED:
    router_v1.include_router(stripe.router, tags=["Stripe"])
if ORGANIZATIONS_ENABLED:
    router_v1.include_router(organizations.router, tags=["Organizations"])
    if ORG_INVITATIONS_ENABLED:
        router_v1.include_router(invitations.router, tags=["Organization Invitations"])
router_v1.include_router(admin.router, tags=["Admin"])
router_v1.include_router(backups.router, tags=["Backups"])
router_v1.include_router(db_health.router, tags=["Database Health"])
if MANAGED_ACCOUNTS_ENABLED:
    router_v1.include_router(managed_account_groups.router, tags=["Managed Accounts"])
router_v1.include_router(app_router)

# Main router combines all versions
router = APIRouter()
router.include_router(router_unversioned)
router.include_router(router_v1)
