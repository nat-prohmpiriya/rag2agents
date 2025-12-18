"""Rate limiting configuration using slowapi with Redis backend."""

import logging

from fastapi import Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """
    Get client IP address, considering proxy headers.

    Args:
        request: FastAPI request object

    Returns:
        Client IP address string
    """
    # Check for forwarded IP (behind proxy/load balancer)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Take the first IP in the chain (original client)
        return forwarded_for.split(",")[0].strip()

    # Check for real IP header (some proxies use this)
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct connection IP
    return get_remote_address(request)


def create_limiter() -> Limiter:
    """
    Create rate limiter with in-memory storage.

    Note: For production with multiple instances, configure Redis with
    REDIS_HOST, REDIS_PORT, and REDIS_PASSWORD environment variables.
    """
    # Use in-memory storage by default for simplicity
    # Redis requires authentication in most setups
    limiter = Limiter(
        key_func=get_client_ip,
        strategy="fixed-window",
    )
    logger.info("Rate limiter initialized with in-memory storage")
    return limiter


# Global limiter instance
limiter = create_limiter()


# Rate limit configurations for different endpoints
class RateLimits:
    """Rate limit configurations for different endpoint types."""

    # Auth endpoints - stricter limits to prevent brute force
    AUTH_LOGIN = "5/minute"  # 5 login attempts per minute
    AUTH_REGISTER = "3/minute"  # 3 registration attempts per minute
    AUTH_REFRESH = "10/minute"  # 10 token refreshes per minute
    AUTH_FORGOT_PASSWORD = "3/minute"  # 3 password reset requests per minute

    # General API endpoints
    API_DEFAULT = "60/minute"  # 60 requests per minute for general endpoints
    API_CHAT = "30/minute"  # 30 chat requests per minute (LLM calls are expensive)
    API_UPLOAD = "10/minute"  # 10 file uploads per minute


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors.

    Returns a JSON response with details about the rate limit.
    """
    from fastapi.responses import JSONResponse

    from app.core.context import get_context

    ctx = get_context()

    return JSONResponse(
        status_code=429,
        content={
            "trace_id": ctx.trace_id,
            "error": "RateLimitExceeded",
            "detail": f"Rate limit exceeded: {exc.detail}",
            "retry_after": getattr(exc, "retry_after", None),
        },
        headers={"Retry-After": str(getattr(exc, "retry_after", 60))},
    )
