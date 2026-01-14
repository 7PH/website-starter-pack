# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
from fastapi import FastAPI, Request
from fastapi.concurrency import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .constants import IS_PROD
from .helpers.db import create_db_and_tables
from .helpers.logging import configure_logging, get_logger, set_request_id
from .helpers.ratelimit import cleanup_entries
from .helpers.security_headers import SecurityHeadersMiddleware
from .helpers.stripe import init_stripe
from .main_ext import extend_app
from .router import router as api_router
from .tasks import register_core_tasks

# Configure structured logging before app startup
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting app")
    create_db_and_tables()
    cleanup_entries()
    init_stripe()
    yield
    logger.info("Stopping app")


# Create FastAPI app instance
app = FastAPI(debug=not IS_PROD, lifespan=lifespan)

# Register scheduled tasks
register_core_tasks(app)


# Add CORS middleware (only needed in development when frontend runs separately)
if not IS_PROD:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add security headers to all responses
app.add_middleware(SecurityHeadersMiddleware)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Add request ID to context for logging."""
    # Use X-Request-ID header if provided, otherwise generate one
    request_id = request.headers.get("X-Request-ID")
    set_request_id(request_id)
    response = await call_next(request)
    return response


@app.exception_handler(RequestValidationError)
async def custom_form_validation_error(request: Request, exc: RequestValidationError):
    """
    Custom handler for request validation errors.
    Reformats the Pydantic validation error messages for better readability and returns a JSON response.
    """
    reformatted_message = []
    for error in exc.errors():
        loc = error["loc"]
        msg = error["msg"]
        # Remove common request types from the error location
        filtered_loc = loc[1:] if loc[0] in ("body", "query", "path") else loc
        field_string = ".".join(filtered_loc)  # Format nested fields using dot-notation
        reformatted_message.append(f"{field_string}: {msg}")

    return JSONResponse(
        content={
            "error": "Validation error",
            "message": ", ".join(reformatted_message),  # User-friendly reformatted message
        },
        status_code=400,
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Custom handler for HTTP exceptions.
    Returns a JSON response with the error detail and status code.
    """
    return JSONResponse(
        content={
            "error": "HTTP error",
            "detail": str(exc.detail),
        },
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch-all handler for unhandled exceptions.
    Prevents stack traces from being exposed to clients while logging
    the full error details server-side for debugging.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred",
        },
        status_code=500,
    )


app.include_router(api_router)

extend_app(app, api_router)
