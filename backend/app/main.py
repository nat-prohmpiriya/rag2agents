import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.core.context import get_context
from app.core.database import instrument_database_engine
from app.core.exceptions import AppException
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.core.telemetry import (
    instrument_app,
    instrument_redis,
    setup_logging,
    setup_metrics,
    setup_telemetry,
)
from app.middleware import MetricsMiddleware, TraceContextMiddleware
from app.routes import (
    agents,
    auth,
    billing,
    chat,
    conversations,
    documents,
    health,
    images,
    notifications,
    profile,
    projects,
    webhooks,
    workflows,
)
from app.routes.admin import audit as admin_audit
from app.routes.admin import dashboard as admin_dashboard
from app.routes.admin import notifications as admin_notifications
from app.routes.admin import plans as admin_plans
from app.routes.admin import settings as admin_settings
from app.routes.admin import subscriptions as admin_subscriptions
from app.routes.admin import system as admin_system
from app.routes.admin import usage as admin_usage
from app.routes.admin import users as admin_users
from app.schemas.base import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup - initialize in order: logging -> tracing -> db -> redis -> metrics
    setup_logging()
    setup_telemetry()
    instrument_database_engine()
    instrument_redis()
    setup_metrics()
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(
    title=settings.app_name,
    description="RAG Agent Platform - Backend API",
    version="0.1.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

# Rate limiter state
app.state.limiter = limiter

# Instrument with OpenTelemetry (must be before other middleware)
instrument_app(app)

# Metrics Middleware (records HTTP request metrics)
app.add_middleware(MetricsMiddleware)

# Trace Context Middleware (creates RequestContext per request)
app.add_middleware(TraceContextMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    ctx = get_context()
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            trace_id=ctx.trace_id,
            error=exc.__class__.__name__,
            detail=exc.message,
        ).model_dump(),
    )


# Rate limit exceeded handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# Routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(profile.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(workflows.router, prefix="/api/v1")
app.include_router(images.router, prefix="/api/v1")

# Admin routers
app.include_router(admin_audit.router, prefix="/api/v1/admin")
app.include_router(admin_dashboard.router, prefix="/api/v1/admin")
app.include_router(admin_notifications.router, prefix="/api/v1/admin")
app.include_router(admin_plans.router, prefix="/api/v1/admin")
app.include_router(admin_settings.router, prefix="/api/v1/admin")
app.include_router(admin_subscriptions.router, prefix="/api/v1/admin")
app.include_router(admin_system.router, prefix="/api/v1/admin")
app.include_router(admin_usage.router, prefix="/api/v1/admin")
app.include_router(admin_users.router, prefix="/api/v1/admin")

# Webhook routers
app.include_router(webhooks.router, prefix="/api/v1")

# Serve static files (frontend) - must be last to not override API routes
if settings.serve_static_files and os.path.exists(settings.static_files_path):
    # Mount static files for assets (js, css, images, etc.)
    app.mount("/_app", StaticFiles(directory=os.path.join(settings.static_files_path, "_app")), name="app_assets")

    # Check if other static directories exist and mount them
    for static_dir in ["fonts", "images", "icons"]:
        static_path = os.path.join(settings.static_files_path, static_dir)
        if os.path.exists(static_path):
            app.mount(f"/{static_dir}", StaticFiles(directory=static_path), name=static_dir)

    # SPA catch-all route - serves index.html for all non-API routes
    @app.get("/{full_path:path}", response_model=None)
    async def serve_spa(full_path: str):
        """Serve SPA for client-side routing."""
        # Skip API routes
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})

        # Try to serve static file first
        static_file = os.path.join(settings.static_files_path, full_path)
        if os.path.isfile(static_file):
            return FileResponse(static_file)

        # Fallback to index.html for SPA routing
        index_path = os.path.join(settings.static_files_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path, media_type="text/html")

        return JSONResponse(status_code=404, content={"detail": "Not Found"})
else:
    # Default root endpoint when not serving static files
    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "RAG Agent Platform API", "version": "0.1.0", "status": "Server is running"}
