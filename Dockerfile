# =============================================================================
# Multi-stage Dockerfile for RAG Agent Platform
# Combines Frontend (SvelteKit) + Backend (FastAPI) in single container
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build Frontend
# -----------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files first for better caching
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies
RUN npm ci --legacy-peer-deps

# Copy source code
COPY frontend/ ./

# Build production bundle
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Build Backend Dependencies
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS backend-builder

WORKDIR /app

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files (including README.md required by pyproject.toml)
COPY backend/pyproject.toml backend/uv.lock backend/README.md ./

# Copy app package for hatchling to find
COPY backend/app ./app

# Create virtual environment and install dependencies
RUN uv sync --frozen --no-dev

# -----------------------------------------------------------------------------
# Stage 3: Final Runtime Image
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy uv for potential runtime use
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy virtual environment from builder
COPY --from=backend-builder /app/.venv /app/.venv

# Copy backend source code
COPY backend/ ./

# Copy frontend build output to static directory
COPY --from=frontend-builder /app/frontend/build /app/static

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
