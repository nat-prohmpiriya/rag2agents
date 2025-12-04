from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.context import get_context
from app.core.exceptions import AppException
from app.core.telemetry import instrument_app, setup_telemetry
from app.middleware import TraceContextMiddleware
from app.routes import (
    agents,
    auth,
    billing,
    chat,
    conversations,
    documents,
    health,
    notifications,
    profile,
    projects,
)
from app.routes import webhooks
from app.routes.admin import audit as admin_audit
from app.routes.admin import dashboard as admin_dashboard
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
    # Startup
    setup_telemetry()
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

# Instrument with OpenTelemetry (must be before other middleware)
instrument_app(app)

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


# Routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(billing.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")

# Admin routers
app.include_router(admin_audit.router, prefix="/api/admin")
app.include_router(admin_dashboard.router, prefix="/api/admin")
app.include_router(admin_plans.router, prefix="/api/admin")
app.include_router(admin_settings.router, prefix="/api/admin")
app.include_router(admin_subscriptions.router, prefix="/api/admin")
app.include_router(admin_system.router, prefix="/api/admin")
app.include_router(admin_usage.router, prefix="/api/admin")
app.include_router(admin_users.router, prefix="/api/admin")

# Webhook routers
app.include_router(webhooks.router, prefix="/api")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "RAG Agent Platform API", "version": "0.1.0", "status": "Server is running"}
