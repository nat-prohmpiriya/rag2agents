from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.schemas.admin import ServiceStatus
from app.services.system_health import (
    check_litellm_health,
    check_postgresql_health,
    check_redis_health,
)

router = APIRouter(prefix="/health")


@router.get("")
async def health_check() -> dict[str, str]:
    """
    Basic health check endpoint.
    Returns healthy if the server is running.
    """
    return {"status": "healthy"}


@router.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | dict]:
    """
    Readiness check endpoint.
    Checks database and LiteLLM connectivity.
    Returns ready only if all critical services are available.
    """
    # Check critical services
    db_health = await check_postgresql_health(db)
    litellm_health = await check_litellm_health()

    # Determine if ready
    is_ready = (
        db_health.status == ServiceStatus.HEALTHY
        and litellm_health.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]
    )

    return {
        "status": "ready" if is_ready else "not_ready",
        "checks": {
            "database": {
                "status": db_health.status.value,
                "response_time_ms": db_health.response_time_ms,
                "error": db_health.error,
            },
            "litellm": {
                "status": litellm_health.status.value,
                "response_time_ms": litellm_health.response_time_ms,
                "models_available": litellm_health.models_available,
                "error": litellm_health.error,
            },
        },
    }


@router.get("/live")
async def liveness_check() -> dict[str, str]:
    """
    Liveness check endpoint.
    Returns alive if the server process is running.
    Used by Kubernetes/Docker to determine if container should be restarted.
    """
    return {"status": "alive"}


@router.get("/detailed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | dict]:
    """
    Detailed health check endpoint.
    Returns status of all services including Redis.
    """
    # Check all services
    db_health = await check_postgresql_health(db)
    litellm_health = await check_litellm_health()
    redis_health = await check_redis_health()

    # Determine overall status
    all_healthy = all(
        h.status == ServiceStatus.HEALTHY
        for h in [db_health, litellm_health, redis_health]
    )
    any_unhealthy = any(
        h.status == ServiceStatus.UNHEALTHY
        for h in [db_health, litellm_health, redis_health]
    )

    if all_healthy:
        overall = "healthy"
    elif any_unhealthy:
        overall = "unhealthy"
    else:
        overall = "degraded"

    return {
        "status": overall,
        "services": {
            "database": {
                "status": db_health.status.value,
                "host": db_health.host,
                "response_time_ms": db_health.response_time_ms,
                "active_connections": db_health.active_connections,
                "max_connections": db_health.max_connections,
                "database_size_mb": db_health.database_size_mb,
                "error": db_health.error,
            },
            "litellm": {
                "status": litellm_health.status.value,
                "url": litellm_health.url,
                "response_time_ms": litellm_health.response_time_ms,
                "models_available": litellm_health.models_available,
                "error": litellm_health.error,
            },
            "redis": {
                "status": redis_health.status.value,
                "host": f"{redis_health.host}:{redis_health.port}",
                "response_time_ms": redis_health.response_time_ms,
                "used_memory_mb": redis_health.used_memory_mb,
                "connected_clients": redis_health.connected_clients,
                "hit_rate": redis_health.hit_rate,
                "error": redis_health.error,
            },
        },
    }
