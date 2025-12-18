"""System health monitoring service."""

import logging
import time
from datetime import UTC, datetime

import httpx
import redis.asyncio as redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.telemetry import traced
from app.schemas.admin import (
    LiteLLMHealth,
    PostgreSQLHealth,
    RedisHealth,
    ServiceStatus,
    SystemHealthResponse,
    SystemMetrics,
)

logger = logging.getLogger(__name__)


@traced()
async def check_litellm_health() -> LiteLLMHealth:
    """Check LiteLLM proxy health status."""
    url = settings.litellm_api_url

    try:
        start_time = time.time()
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{url}/health")
            response_time_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                # Try to get model count
                models_count = 0
                try:
                    models_response = await client.get(
                        f"{url}/models",
                        headers={"Authorization": f"Bearer {settings.litellm_api_key}"}
                    )
                    if models_response.status_code == 200:
                        models_data = models_response.json()
                        if "data" in models_data:
                            models_count = len(models_data["data"])
                except httpx.HTTPError as e:
                    logger.debug(f"Failed to fetch model count: {e}")
                except Exception as e:
                    logger.debug(f"Unexpected error fetching model count: {e}")

                return LiteLLMHealth(
                    status=ServiceStatus.HEALTHY,
                    url=url,
                    response_time_ms=round(response_time_ms, 2),
                    models_available=models_count,
                )
            else:
                return LiteLLMHealth(
                    status=ServiceStatus.DEGRADED,
                    url=url,
                    response_time_ms=round(response_time_ms, 2),
                    error=f"HTTP {response.status_code}",
                )
    except httpx.TimeoutException:
        return LiteLLMHealth(
            status=ServiceStatus.UNHEALTHY,
            url=url,
            error="Connection timeout",
        )
    except httpx.ConnectError:
        return LiteLLMHealth(
            status=ServiceStatus.UNHEALTHY,
            url=url,
            error="Connection refused",
        )
    except Exception as e:
        return LiteLLMHealth(
            status=ServiceStatus.UNHEALTHY,
            url=url,
            error=str(e),
        )


@traced()
async def check_postgresql_health(db: AsyncSession) -> PostgreSQLHealth:
    """Check PostgreSQL database health status."""
    host = settings.database_url.split("@")[-1].split("/")[0] if "@" in settings.database_url else "localhost"

    try:
        start_time = time.time()

        # Test connection with simple query
        await db.execute(text("SELECT 1"))
        response_time_ms = (time.time() - start_time) * 1000

        # Get connection stats
        result = await db.execute(text("""
            SELECT
                numbackends as active_connections,
                (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections
            FROM pg_stat_database
            WHERE datname = current_database()
        """))
        row = result.fetchone()
        active_connections = row[0] if row else 0
        max_connections = row[1] if row else 100

        # Get database size
        size_result = await db.execute(text("""
            SELECT pg_database_size(current_database()) / 1024.0 / 1024.0 as size_mb
        """))
        size_row = size_result.fetchone()
        database_size_mb = round(size_row[0], 2) if size_row else 0

        return PostgreSQLHealth(
            status=ServiceStatus.HEALTHY,
            host=host,
            active_connections=active_connections,
            max_connections=max_connections,
            database_size_mb=database_size_mb,
            response_time_ms=round(response_time_ms, 2),
        )
    except Exception as e:
        return PostgreSQLHealth(
            status=ServiceStatus.UNHEALTHY,
            host=host,
            error=str(e),
        )


@traced()
async def check_redis_health() -> RedisHealth:
    """Check Redis health status."""
    host = settings.redis_host
    port = settings.redis_port

    try:
        start_time = time.time()

        r = redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
            socket_timeout=5.0,
        )

        # Test connection
        await r.ping()
        response_time_ms = (time.time() - start_time) * 1000

        # Get Redis info
        info = await r.info()

        used_memory_mb = round(info.get("used_memory", 0) / 1024 / 1024, 2)
        max_memory = info.get("maxmemory", 0)
        max_memory_mb = round(max_memory / 1024 / 1024, 2) if max_memory > 0 else 0
        connected_clients = info.get("connected_clients", 0)

        # Calculate hit rate
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        hit_rate = round((hits / total * 100), 2) if total > 0 else 0

        await r.aclose()

        return RedisHealth(
            status=ServiceStatus.HEALTHY,
            host=host,
            port=port,
            used_memory_mb=used_memory_mb,
            max_memory_mb=max_memory_mb,
            connected_clients=connected_clients,
            hit_rate=hit_rate,
            response_time_ms=round(response_time_ms, 2),
        )
    except redis.ConnectionError:
        return RedisHealth(
            status=ServiceStatus.UNHEALTHY,
            host=host,
            port=port,
            error="Connection refused",
        )
    except redis.TimeoutError:
        return RedisHealth(
            status=ServiceStatus.UNHEALTHY,
            host=host,
            port=port,
            error="Connection timeout",
        )
    except Exception as e:
        return RedisHealth(
            status=ServiceStatus.UNHEALTHY,
            host=host,
            port=port,
            error=str(e),
        )


def _determine_overall_status(
    litellm: LiteLLMHealth,
    postgresql: PostgreSQLHealth,
    redis_health: RedisHealth,
) -> ServiceStatus:
    """Determine overall system health status."""
    statuses = [litellm.status, postgresql.status, redis_health.status]

    if all(s == ServiceStatus.HEALTHY for s in statuses):
        return ServiceStatus.HEALTHY
    elif any(s == ServiceStatus.UNHEALTHY for s in statuses):
        return ServiceStatus.UNHEALTHY
    elif any(s == ServiceStatus.DEGRADED for s in statuses):
        return ServiceStatus.DEGRADED
    else:
        return ServiceStatus.UNKNOWN


@traced()
async def get_system_health(db: AsyncSession) -> SystemHealthResponse:
    """Get complete system health status."""
    # Check all services
    litellm = await check_litellm_health()
    postgresql = await check_postgresql_health(db)
    redis_health = await check_redis_health()

    # Determine overall status
    overall_status = _determine_overall_status(litellm, postgresql, redis_health)

    return SystemHealthResponse(
        overall_status=overall_status,
        timestamp=datetime.now(UTC),
        litellm=litellm,
        postgresql=postgresql,
        redis=redis_health,
    )


@traced()
async def get_system_metrics(db: AsyncSession) -> SystemMetrics:
    """Get system performance metrics."""
    # TODO: Implement actual metrics collection from monitoring system
    # For now, return placeholder values
    return SystemMetrics(
        requests_per_second=0,
        avg_response_time_ms=0,
        error_rate_percent=0,
        active_users=0,
        uptime_seconds=0,
    )
