# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""Pydantic schemas for database health monitoring."""

from datetime import datetime

from pydantic import BaseModel


class TableStats(BaseModel):
    """Statistics for a database table."""

    name: str
    size: int
    size_pretty: str
    row_count: int
    dead_tuples: int
    seq_scans: int
    idx_scans: int
    last_vacuum: datetime | None


class IndexStats(BaseModel):
    """Statistics for a database index."""

    name: str
    table: str
    size: int
    size_pretty: str
    scans: int
    is_unused: bool


class Recommendation(BaseModel):
    """An actionable recommendation for database optimization."""

    type: str  # 'missing_index', 'vacuum_needed', 'unused_index', 'cache_low'
    severity: str  # 'info', 'warning', 'critical'
    table: str | None
    message: str
    action: str


class DatabaseHealthResponse(BaseModel):
    """Complete database health response."""

    database_size: int
    database_size_pretty: str
    active_connections: int
    max_connections: int
    cache_hit_ratio: float
    tables: list[TableStats]
    indexes: list[IndexStats]
    recommendations: list[Recommendation]
