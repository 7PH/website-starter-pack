# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

Base = declarative_base()

db_url = f"postgresql://{os.environ["APP_DB_USER"]}:{os.environ["APP_DB_PASSWORD"]}@db/{os.environ["APP_DB_NAME"]}"


def _build_options_string() -> str:
    """Build the libpq `options` connect arg from per-connection server settings.

    `0` disables a given timeout. Both default to 30s to cap pathological queries
    and transactions that block connection-pool slots.
    """
    parts: list[str] = []
    statement_timeout_ms = int(os.environ.get("DB_STATEMENT_TIMEOUT_MS", "30000"))
    idle_tx_timeout_ms = int(os.environ.get("DB_IDLE_IN_TRANSACTION_TIMEOUT_MS", "30000"))
    if statement_timeout_ms > 0:
        parts.append(f"-c statement_timeout={statement_timeout_ms}")
    if idle_tx_timeout_ms > 0:
        parts.append(f"-c idle_in_transaction_session_timeout={idle_tx_timeout_ms}")
    return " ".join(parts)


connect_args: dict = {}
options = _build_options_string()
if options:
    connect_args["options"] = options

engine = create_engine(
    db_url,
    echo=os.environ.get("DB_ECHO", "false").lower() == "true",
    poolclass=QueuePool,
    pool_size=int(os.environ.get("DB_POOL_SIZE", "5")),
    max_overflow=int(os.environ.get("DB_MAX_OVERFLOW", "10")),
    pool_timeout=int(os.environ.get("DB_POOL_TIMEOUT", "30")),
    pool_recycle=int(os.environ.get("DB_POOL_RECYCLE", "1800")),
    pool_pre_ping=True,
    connect_args=connect_args,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_db_and_tables():
    Base.metadata.create_all(engine)


def get_session():
    with SessionLocal() as session:
        yield session
