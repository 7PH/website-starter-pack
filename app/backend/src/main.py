# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
from fastapi import FastAPI, Request
from fastapi.concurrency import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .constants import IS_PROD
from .helpers.db import create_db_and_tables
from .helpers.ratelimit import cleanup_entries
from .router import router as api_router
from .tasks import register_core_tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting app")
    create_db_and_tables()
    cleanup_entries()
    yield
    print("Stopping app")


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
            "message": ", ".join(
                reformatted_message
            ),  # User-friendly reformatted message
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


app.include_router(api_router)
