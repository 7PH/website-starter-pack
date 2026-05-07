"""
Project-specific app extensions.

Use this file to customize the FastAPI app and router after core setup.
This is called after all core middleware and routes are configured.

Examples:
- Add API v2 routes
- Add custom middleware
- Add exception handlers
- Register additional startup/shutdown events
"""

from fastapi import APIRouter, FastAPI


def extend_app(app: FastAPI, router: APIRouter) -> None:
    """
    Extend the FastAPI app with project-specific customizations.

    Args:
        app: The FastAPI application instance (fully configured)
        router: The main API router (already includes v1 routes)

    Examples:
        # Add v2 API routes
        from .controllers import my_v2_routes
        router_v2 = APIRouter(prefix="/v2")
        router_v2.include_router(my_v2_routes.router, tags=["V2"])
        router.include_router(router_v2)

        # Add custom middleware
        from .helpers.my_middleware import MyMiddleware
        app.add_middleware(MyMiddleware)

        # Add exception handler
        @app.exception_handler(MyCustomException)
        async def my_exception_handler(request, exc):
            return JSONResponse({"error": str(exc)}, status_code=400)
    """
    # Sign-in by access code: opt in to the default resolver (looks up the
    # access_codes table). Apps with custom semantics register their own
    # @on(AccessCodeResolution) handler instead.
    # Only registered when MANAGED_ACCOUNTS_ENABLED is true so apps that
    # don't use managed accounts get a clean 404 on /auth/code.
    from .constants import MANAGED_ACCOUNTS_ENABLED

    if MANAGED_ACCOUNTS_ENABLED:
        from .helpers.access_codes import register_default_access_code_resolver

        register_default_access_code_resolver()
