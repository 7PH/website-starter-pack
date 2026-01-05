# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

"""
Database health controller for monitoring and optimization recommendations.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..helpers.auth import get_current_admin
from ..helpers.db import get_session
from ..models.db_health import (
    DatabaseHealthResponse,
    IndexStats,
    Recommendation,
    TableStats,
)
from ..models.user import UserRead

router = APIRouter(prefix="/admin/db-health")


def format_bytes(size: int) -> str:
    """Format bytes to human-readable string."""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"


def get_database_size(session: Session) -> tuple[int, str]:
    """Get the total database size."""
    result = session.execute(text("SELECT pg_database_size(current_database())"))
    size = result.scalar() or 0
    return size, format_bytes(size)


def get_connection_stats(session: Session) -> tuple[int, int]:
    """Get active connections and max connections."""
    result = session.execute(
        text("""
        SELECT
            (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()) as active,
            (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max
        """)
    )
    row = result.fetchone()
    return row[0] if row else 0, row[1] if row else 100


def get_cache_hit_ratio(session: Session) -> float:
    """Get the buffer cache hit ratio."""
    result = session.execute(
        text("""
        SELECT
            CASE
                WHEN sum(heap_blks_hit) + sum(heap_blks_read) = 0 THEN 100.0
                ELSE ROUND(100.0 * sum(heap_blks_hit) /
                     (sum(heap_blks_hit) + sum(heap_blks_read)), 2)
            END as ratio
        FROM pg_statio_user_tables
        """)
    )
    ratio = result.scalar()
    return float(ratio) if ratio is not None else 100.0


def get_table_stats(session: Session) -> list[TableStats]:
    """Get statistics for all user tables."""
    result = session.execute(
        text("""
        SELECT
            relname,
            pg_total_relation_size(relid) as size,
            n_live_tup as row_count,
            n_dead_tup as dead_tuples,
            seq_scan,
            idx_scan,
            last_vacuum
        FROM pg_stat_user_tables
        ORDER BY pg_total_relation_size(relid) DESC
        """)
    )

    tables = []
    for row in result.fetchall():
        tables.append(
            TableStats(
                name=row[0],
                size=row[1] or 0,
                size_pretty=format_bytes(row[1] or 0),
                row_count=row[2] or 0,
                dead_tuples=row[3] or 0,
                seq_scans=row[4] or 0,
                idx_scans=row[5] or 0,
                last_vacuum=row[6],
            )
        )
    return tables


def get_index_stats(session: Session) -> list[IndexStats]:
    """Get statistics for all user indexes."""
    result = session.execute(
        text("""
        SELECT
            indexrelname,
            relname as tablename,
            pg_relation_size(indexrelid) as size,
            idx_scan
        FROM pg_stat_user_indexes
        ORDER BY pg_relation_size(indexrelid) DESC
        """)
    )

    indexes = []
    for row in result.fetchall():
        scans = row[3] or 0
        indexes.append(
            IndexStats(
                name=row[0],
                table=row[1],
                size=row[2] or 0,
                size_pretty=format_bytes(row[2] or 0),
                scans=scans,
                is_unused=scans == 0,
            )
        )
    return indexes


def generate_recommendations(
    tables: list[TableStats],
    indexes: list[IndexStats],
    cache_ratio: float,
) -> list[Recommendation]:
    """Generate actionable recommendations based on database stats."""
    recommendations = []

    # Missing indexes: high seq_scan with significant rows
    for t in tables:
        if t.row_count > 1000 and t.idx_scans > 0:
            ratio = t.seq_scans / max(t.idx_scans, 1)
            if ratio > 10:
                recommendations.append(
                    Recommendation(
                        type="missing_index",
                        severity="warning",
                        table=t.name,
                        message=f"Table '{t.name}' has {t.seq_scans:,} sequential scans vs {t.idx_scans:,} index scans",
                        action="Consider adding an index on frequently queried columns",
                    )
                )

    # Vacuum needed: high dead tuple ratio
    for t in tables:
        total = t.row_count + t.dead_tuples
        if total > 0:
            ratio = t.dead_tuples / total
            if ratio > 0.1:
                severity = "critical" if ratio > 0.2 else "warning"
                recommendations.append(
                    Recommendation(
                        type="vacuum_needed",
                        severity=severity,
                        table=t.name,
                        message=f"Table '{t.name}' has {ratio:.0%} dead tuples ({t.dead_tuples:,} dead / {total:,} total)",
                        action="Run VACUUM ANALYZE on this table",
                    )
                )

    # Unused indexes (only flag if > 1KB to avoid noise from small tables)
    for i in indexes:
        if i.is_unused and i.size > 1024:
            recommendations.append(
                Recommendation(
                    type="unused_index",
                    severity="info",
                    table=i.table,
                    message=f"Index '{i.name}' on '{i.table}' has never been used ({i.size_pretty})",
                    action="Consider dropping this index to save space",
                )
            )

    # Low cache hit ratio
    if cache_ratio < 95:
        severity = "critical" if cache_ratio < 90 else "warning"
        recommendations.append(
            Recommendation(
                type="cache_low",
                severity=severity,
                table=None,
                message=f"Cache hit ratio is {cache_ratio:.1f}%",
                action="Consider increasing shared_buffers in PostgreSQL config",
            )
        )

    # All good message if no issues
    if not recommendations:
        recommendations.append(
            Recommendation(
                type="all_good",
                severity="info",
                table=None,
                message="No optimization issues detected",
                action="Database is healthy",
            )
        )

    return recommendations


@router.get("", response_model=DatabaseHealthResponse)
def get_database_health(
    session: Session = Depends(get_session),
    admin: UserRead = Depends(get_current_admin),
):
    """Get comprehensive database health metrics and recommendations."""
    # Gather all stats
    db_size, db_size_pretty = get_database_size(session)
    active_conns, max_conns = get_connection_stats(session)
    cache_ratio = get_cache_hit_ratio(session)
    tables = get_table_stats(session)
    indexes = get_index_stats(session)

    # Generate recommendations
    recommendations = generate_recommendations(tables, indexes, cache_ratio)

    return DatabaseHealthResponse(
        database_size=db_size,
        database_size_pretty=db_size_pretty,
        active_connections=active_conns,
        max_connections=max_conns,
        cache_hit_ratio=cache_ratio,
        tables=tables,
        indexes=indexes,
        recommendations=recommendations,
    )
