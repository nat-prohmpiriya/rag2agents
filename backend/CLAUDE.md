# Backend Instructions

> **Full documentation**: See `CLAUDE.full.md` or `../.claude/backend.md`

## Tech Stack
FastAPI + Python 3.12+ + SQLAlchemy async + PostgreSQL + Pydantic v2

## Architecture

```
Request → Routes → Services → Models → Response
            ↓          ↓
       (validate)  (business logic)
```

## Critical Rules

### 1. Type Hints (Required)
```python
async def get_user(user_id: int) -> User | None:
    ...
```

### 2. BaseResponse Wrapper (Required)
```python
@router.get("/{user_id}")
async def get_user(user_id: int) -> BaseResponse[UserResponse]:
    ctx = get_context()
    return BaseResponse(
        trace_id=ctx.trace_id,
        data=UserResponse.model_validate(user),
    )
```

### 3. Pydantic v2
```python
class UserResponse(BaseModel):
    id: int
    email: str
    model_config = ConfigDict(from_attributes=True)
```

### 4. @traced Decorator
```python
@traced()
async def create_user(db: AsyncSession, data: UserCreate) -> User:
    ...
```

## Structure

| Layer | Purpose |
|-------|---------|
| `routes/` | HTTP handling only |
| `services/` | Business logic, DB queries |
| `models/` | SQLAlchemy ORM |
| `schemas/` | Pydantic validation |

## Storage

Document files are stored using the configured storage service:

| Type | Description | Persistence |
|------|-------------|-------------|
| `local` | Local filesystem (`./uploads`) | ❌ Lost on container restart |
| `minio` | MinIO S3-compatible storage | ✅ Persistent |

**Important**: Production MUST use `STORAGE_TYPE=minio` to prevent file loss on container restart.

### Configuration

```bash
# For production (MinIO)
STORAGE_TYPE=minio
MINIO_ENDPOINT=minio.dackbox.com
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_DOCUMENTS_BUCKET=ragagent-documents
MINIO_SECURE=true
```

### Storage Service

```python
from app.services.storage import get_storage_service

storage = get_storage_service()
path = await storage.upload(file_bytes, filename, user_id)
content = await storage.download(path)
await storage.delete(path)
```

## Commands

```bash
uv run uvicorn app.main:app --reload  # Dev
uv run alembic upgrade head           # Migrate
uv run pytest                         # Test
uv run ruff check . --fix             # Lint
```
