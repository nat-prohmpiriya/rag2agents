"""OpenTelemetry setup and utilities for tracing, logging, and metrics."""

import json
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from app.config import settings

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")

# Module-level variables for lazy initialization
_tracer = None
_meter = None
_resource = None

# Metrics instruments (initialized lazily)
_http_request_counter = None
_http_request_duration = None


def _get_resource():
    """Get shared OpenTelemetry resource."""
    global _resource
    if _resource is not None:
        return _resource

    try:
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource

        _resource = Resource(
            attributes={
                SERVICE_NAME: settings.otel_service_name,
                "service.version": "0.1.0",
                "deployment.environment": settings.app_env,
            }
        )
        return _resource
    except ImportError:
        return None


def setup_telemetry() -> None:
    """Initialize OpenTelemetry tracing."""
    if not settings.otel_enabled:
        logger.info("OpenTelemetry is disabled")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = _get_resource()
        if resource is None:
            logger.warning("Failed to create resource, tracing disabled")
            return

        # Setup tracer provider
        provider = TracerProvider(resource=resource)

        # Configure OTLP exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_endpoint,
            insecure=True,
        )

        # Add span processor
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        # Set global tracer provider
        trace.set_tracer_provider(provider)

        logger.info(
            f"OpenTelemetry tracing initialized: service={settings.otel_service_name}, "
            f"endpoint={settings.otel_exporter_endpoint}"
        )
    except ImportError:
        logger.warning("OpenTelemetry tracing packages not installed")
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry tracing: {e}")


def setup_logging() -> None:
    """Initialize OpenTelemetry logging with OTLP export."""
    if not settings.otel_enabled:
        return

    try:
        from opentelemetry._logs import set_logger_provider
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
            OTLPLogExporter,
        )
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

        resource = _get_resource()
        if resource is None:
            logger.warning("Failed to create resource, logging export disabled")
            return

        # Setup logger provider
        logger_provider = LoggerProvider(resource=resource)
        set_logger_provider(logger_provider)

        # Configure OTLP exporter for logs
        log_exporter = OTLPLogExporter(
            endpoint=settings.otel_exporter_endpoint,
            insecure=True,
        )

        # Add log record processor
        logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(log_exporter)
        )

        # Get log level from config
        log_level = getattr(logging, settings.otel_log_level.upper(), logging.INFO)

        # Add handler to root logger
        handler = LoggingHandler(
            level=log_level,
            logger_provider=logger_provider,
        )
        logging.getLogger().addHandler(handler)

        logger.info("OpenTelemetry logging initialized")
    except ImportError:
        logger.warning("OpenTelemetry logging packages not installed")
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry logging: {e}")


def setup_metrics() -> None:
    """Initialize OpenTelemetry metrics with OTLP export."""
    global _meter, _http_request_counter, _http_request_duration

    if not settings.otel_enabled:
        return

    try:
        from opentelemetry import metrics
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

        resource = _get_resource()
        if resource is None:
            logger.warning("Failed to create resource, metrics disabled")
            return

        # Configure OTLP exporter for metrics
        metric_exporter = OTLPMetricExporter(
            endpoint=settings.otel_exporter_endpoint,
            insecure=True,
        )

        # Create periodic metric reader
        metric_reader = PeriodicExportingMetricReader(
            metric_exporter,
            export_interval_millis=settings.otel_metrics_export_interval_ms,
        )

        # Setup meter provider
        provider = MeterProvider(
            resource=resource,
            metric_readers=[metric_reader],
        )
        metrics.set_meter_provider(provider)

        # Initialize meter
        _meter = metrics.get_meter(settings.otel_service_name, "0.1.0")

        # Create HTTP metrics instruments
        _http_request_counter = _meter.create_counter(
            name="http_requests_total",
            description="Total number of HTTP requests",
            unit="1",
        )

        _http_request_duration = _meter.create_histogram(
            name="http_request_duration_seconds",
            description="HTTP request duration in seconds",
            unit="s",
        )

        logger.info("OpenTelemetry metrics initialized")
    except ImportError:
        logger.warning("OpenTelemetry metrics packages not installed")
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry metrics: {e}")


def get_http_request_counter():
    """Get HTTP request counter metric."""
    return _http_request_counter


def get_http_request_duration():
    """Get HTTP request duration histogram metric."""
    return _http_request_duration


def get_meter(name: str | None = None):
    """
    Get a meter instance for creating custom metrics.

    Args:
        name: Optional meter name. Defaults to service name.

    Returns:
        Meter instance or None if metrics disabled.
    """
    if not settings.otel_enabled or _meter is None:
        return None
    return _meter


def instrument_app(app) -> None:
    """Instrument FastAPI app with OpenTelemetry."""
    if not settings.otel_enabled:
        return

    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        # FastAPI auto-instrumentation
        FastAPIInstrumentor.instrument_app(app)

        # HTTPX (for LiteLLM calls)
        HTTPXClientInstrumentor().instrument()

        logger.info("FastAPI and HTTPX instrumented with OpenTelemetry")
    except ImportError:
        logger.warning("OpenTelemetry instrumentation packages not installed")
    except Exception as e:
        logger.error(f"Failed to instrument app: {e}")


def instrument_database(engine) -> None:
    """Instrument SQLAlchemy engine with OpenTelemetry."""
    if not settings.otel_enabled:
        return

    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
        logger.info("SQLAlchemy instrumented with OpenTelemetry")
    except ImportError:
        logger.warning("SQLAlchemy instrumentation package not installed")
    except Exception as e:
        logger.error(f"Failed to instrument database: {e}")


def get_tracer(name: str = __name__):
    """Get a tracer instance for creating spans."""
    if not settings.otel_enabled:
        return None

    try:
        from opentelemetry import trace

        return trace.get_tracer(name)
    except ImportError:
        return None


def span_set_data(span, data: dict[str, Any]) -> None:
    """
    Set span attribute with JSON data.

    Args:
        span: OTEL span instance
        data: Dictionary to store as JSON string
    """
    if span is None:
        return

    try:
        span.set_attribute(
            "data", json.dumps(data, ensure_ascii=False, default=str)
        )
    except Exception as e:
        logger.warning(f"Failed to set span data: {e}")


def traced(
    name: str | None = None,
    skip_input: bool = False,
    skip_output: bool = False,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to trace function execution with OTEL.

    Args:
        name: Custom span name (defaults to function name)
        skip_input: Skip logging input parameters (for sensitive data)
        skip_output: Skip logging output (for large responses)

    Usage:
        @traced()
        async def create_order(data: OrderCreate) -> Order:
            ...

        @traced(skip_input=True)  # For functions with sensitive data
        async def authenticate_user(email: str, password: str) -> User:
            ...
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        if not settings.otel_enabled:
            return func

        span_name = name or func.__name__
        tracer = get_tracer(func.__module__)

        if tracer is None:
            return func

        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with tracer.start_as_current_span(span_name) as span:
                # Log input (skip sensitive data)
                if not skip_input and kwargs:
                    input_data = _serialize_kwargs(kwargs)
                    span_set_data(span, {"input": input_data})

                try:
                    result = await func(*args, **kwargs)

                    # Log output
                    if not skip_output and result is not None:
                        output_data = _serialize_result(result)
                        span_set_data(span, {"output": output_data})

                    return result
                except Exception as e:
                    span.record_exception(e)
                    raise

        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with tracer.start_as_current_span(span_name) as span:
                if not skip_input and kwargs:
                    input_data = _serialize_kwargs(kwargs)
                    span_set_data(span, {"input": input_data})

                try:
                    result = func(*args, **kwargs)

                    if not skip_output and result is not None:
                        output_data = _serialize_result(result)
                        span_set_data(span, {"output": output_data})

                    return result
                except Exception as e:
                    span.record_exception(e)
                    raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def _serialize_kwargs(kwargs: dict) -> dict:
    """Serialize function kwargs for logging."""
    result = {}
    for key, value in kwargs.items():
        # Skip db sessions and other non-serializable objects
        if key in ("db", "session", "request", "background_tasks"):
            continue
        try:
            if hasattr(value, "model_dump"):
                result[key] = value.model_dump()
            elif hasattr(value, "__dict__"):
                result[key] = str(value)
            else:
                result[key] = value
        except Exception:
            result[key] = str(value)
    return result


def _serialize_result(result: Any) -> Any:
    """Serialize function result for logging."""
    try:
        if hasattr(result, "model_dump"):
            return result.model_dump()
        elif isinstance(result, (dict, list, str, int, float, bool)):
            return result
        else:
            return str(result)
    except Exception:
        return str(result)
