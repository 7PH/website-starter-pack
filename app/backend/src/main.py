from fastapi import FastAPI, Request
from fastapi.concurrency import asynccontextmanager
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from starlette.exceptions import HTTPException as StarletteHTTPException

from .core.constant import IS_PROD, PUBLIC_PROTOCOL, PUBLIC_URL
from .core.helpers.ratelimit import cleanup_entries
from .db import create_db_and_tables
from .router import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting app")
    create_db_and_tables()
    cleanup_entries()
    yield
    print("Stopping app")


@repeat_every(wait_first=True, seconds=300)  # Run every 5 minutes
def periodic_cleanup():
    cleanup_entries()


# Create FastAPI app instance
app = FastAPI(debug=not IS_PROD, lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"{PUBLIC_PROTOCOL}://frontend",
        PUBLIC_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom exception handlers
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    print(f"HTTP Exception occurred: {repr(exc)}")
    return await http_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    print(f"Validation Error: {exc}")
    return await request_validation_exception_handler(request, exc)


app.include_router(api_router)
