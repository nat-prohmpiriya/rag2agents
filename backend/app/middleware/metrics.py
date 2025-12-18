"""Metrics middleware for recording HTTP request metrics."""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.telemetry import get_http_request_counter, get_http_request_duration


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware that records HTTP request metrics.

    Records:
    - http_requests_total: Counter of total HTTP requests
    - http_request_duration_seconds: Histogram of request durations
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Get metrics instruments
        counter = get_http_request_counter()
        histogram = get_http_request_duration()

        # If metrics not initialized, just pass through
        if counter is None or histogram is None:
            return await call_next(request)

        # Record start time
        start_time = time.perf_counter()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.perf_counter() - start_time

        # Normalize path to reduce cardinality (remove UUIDs, IDs)
        path = self._normalize_path(request.url.path)

        # Prepare attributes
        attributes = {
            "method": request.method,
            "path": path,
            "status_code": str(response.status_code),
        }

        # Record metrics
        counter.add(1, attributes)
        histogram.record(duration, attributes)

        return response

    def _normalize_path(self, path: str) -> str:
        """
        Normalize path to reduce metric cardinality.

        Replaces UUIDs and numeric IDs with placeholders.
        """
        import re

        # Replace UUIDs
        path = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "{id}",
            path,
            flags=re.IGNORECASE,
        )

        # Replace numeric IDs (sequences of digits)
        path = re.sub(r"/\d+(?=/|$)", "/{id}", path)

        return path
