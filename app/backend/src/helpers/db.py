# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

Base = declarative_base()

db_url = f"postgresql://{os.environ["APP_DB_USER"]}:{os.environ["APP_DB_PASSWORD"]}@db/{os.environ["APP_DB_NAME"]}"

# Connection pool configuration
# - pool_size: Number of permanent connections to keep (default: 5)
# - max_overflow: Additional connections allowed when pool is full (default: 10)
# - pool_timeout: Seconds to wait for a connection before error (default: 30)
# - pool_recycle: Recycle connections after N seconds to avoid stale connections (default: 1800 = 30 min)
# - pool_pre_ping: Test connections before use to detect disconnects (default: True)
engine = create_engine(
    db_url,
    echo=os.environ.get("DB_ECHO", "false").lower() == "true",
    poolclass=QueuePool,
    pool_size=int(os.environ.get("DB_POOL_SIZE", "5")),
    max_overflow=int(os.environ.get("DB_MAX_OVERFLOW", "10")),
    pool_timeout=int(os.environ.get("DB_POOL_TIMEOUT", "30")),
    pool_recycle=int(os.environ.get("DB_POOL_RECYCLE", "1800")),
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_db_and_tables():
    Base.metadata.create_all(engine)


def get_session():
    with SessionLocal() as session:
        yield session
