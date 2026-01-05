# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Structured JSON logging configuration.
Provides consistent, parseable logs for production environments.
"""

import json
import logging
import os
import sys
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

# Context variable for request ID (thread-safe)
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    """Get the current request ID from context."""
    return request_id_var.get()


def set_request_id(request_id: str | None = None) -> str:
    """Set the request ID in context. Generates one if not provided."""
    if request_id is None:
        request_id = str(uuid.uuid4())[:8]
    request_id_var.set(request_id)
    return request_id


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request ID if available
        request_id = get_request_id()
        if request_id:
            log_data["request_id"] = request_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add any extra fields
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


class StandardFormatter(logging.Formatter):
    """Standard text formatter with request ID support."""

    def format(self, record: logging.LogRecord) -> str:
        request_id = get_request_id()
        prefix = f"[{request_id}] " if request_id else ""
        return f"{prefix}{super().format(record)}"


def configure_logging(json_format: bool | None = None, level: str = "INFO") -> None:
    """
    Configure application logging.

    Args:
        json_format: Use JSON format (default: True in production, False in dev)
        level: Log level (default: INFO)
    """
    # Auto-detect format based on environment
    if json_format is None:
        json_format = os.environ.get("LOG_FORMAT", "text").lower() == "json"

    # Get log level from env or param
    level = os.environ.get("LOG_LEVEL", level).upper()

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Set formatter
    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            StandardFormatter("%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

    # Reduce noise from third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if os.environ.get("DB_ECHO", "false").lower() == "true" else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)
