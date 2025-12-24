# 05 - API Design & Security: Building a Production-Ready API

---

## 🌐 "อธิบาย API Design ของระบบหน่อย"

### RESTful Resource Structure

```
/api/v1
├── /auth
│   ├── POST /register        # Create account
│   ├── POST /login           # Get tokens
│   ├── POST /refresh         # Refresh access token
│   └── POST /logout          # Invalidate tokens
│
├── /documents
│   ├── GET /                 # List user's documents
│   ├── POST /                # Upload document
│   ├── GET /{id}             # Get document details
│   ├── DELETE /{id}          # Delete document
│   └── GET /{id}/chunks      # Get document chunks
│
├── /chat
│   ├── POST /                # Non-streaming chat
│   └── POST /stream          # SSE streaming chat
│
├── /conversations
│   ├── GET /                 # List conversations
│   ├── POST /                # Create conversation
│   ├── GET /{id}             # Get conversation with messages
│   └── DELETE /{id}          # Delete conversation
│
├── /agents
│   ├── GET /                 # List agents
│   ├── POST /                # Create agent
│   ├── GET /{slug}           # Get agent by slug
│   ├── PUT /{slug}           # Update agent
│   └── DELETE /{slug}        # Delete agent
│
├── /workflows
│   ├── GET /                 # List workflows
│   ├── POST /                # Create workflow
│   ├── GET /{id}             # Get workflow
│   ├── PUT /{id}             # Update workflow
│   ├── DELETE /{id}          # Delete workflow
│   └── POST /{id}/execute    # Execute workflow
│
├── /billing
│   ├── GET /plans            # Available plans
│   ├── POST /checkout        # Create checkout session
│   ├── GET /portal           # Customer portal URL
│   └── GET /usage            # Usage statistics
│
└── /admin  (superuser only)
    ├── GET /users            # List all users
    ├── GET /users/{id}       # Get user details
    ├── PUT /users/{id}       # Update user
    ├── GET /audit-logs       # Audit logs
    └── GET /stats            # System statistics
```

---

## 📦 BaseResponse: "Consistent API Responses"

### The Problem with Inconsistent Responses

```python
# ❌ Different endpoints, different shapes
GET /users/1      → {"id": 1, "name": "John"}
GET /documents/1  → {"document": {"id": 1, ...}}
POST /upload      → {"success": true, "data": {...}}
GET /error        → {"error": "Not found"}  # Different structure!

# Frontend has to handle each case differently
```

### The Solution: BaseResponse Wrapper

```python
# schemas/base.py
from pydantic import BaseModel
from typing import TypeVar, Generic

T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    trace_id: str
    data: T | None = None
    error: str | None = None


# Usage in routes
@router.get("/documents/{id}")
async def get_document(id: UUID, db: AsyncSession = Depends(get_db)) -> BaseResponse[DocumentResponse]:
    ctx = get_context()
    document = await document_service.get_by_id(db, id)

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=DocumentResponse.model_validate(document)
    )
```

### Consistent Response Format

```json
// Success
{
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "id": "123",
    "filename": "report.pdf",
    "status": "ready"
  },
  "error": null
}

// Error
{
  "trace_id": "550e8400-e29b-41d4-a716-446655440001",
  "data": null,
  "error": "Document not found"
}
```

### Benefits

1. **Frontend Simplicity** — Always know the response shape
2. **Distributed Tracing** — trace_id links request across services
3. **Error Handling** — Consistent error format
4. **Type Safety** — Generic type parameter for data

---

## 🔐 Authentication: "JWT Implementation Deep Dive"

### The Auth Flow

```
┌──────────┐     POST /login      ┌──────────┐
│  Client  │ ──────────────────→  │  Server  │
│          │  {email, password}   │          │
└──────────┘                      └──────────┘
                                       │
                                       │ Verify credentials
                                       │ Generate tokens
                                       ▼
┌──────────┐   {access, refresh}  ┌──────────┐
│  Client  │ ←──────────────────  │  Server  │
│          │                      │          │
└──────────┘                      └──────────┘
     │
     │ Store tokens
     │ (localStorage/httpOnly cookie)
     ▼
┌──────────┐  GET /api/protected  ┌──────────┐
│  Client  │ ──────────────────→  │  Server  │
│          │  Authorization:      │          │
│          │  Bearer <access>     │          │
└──────────┘                      └──────────┘
                                       │
                                       │ Verify JWT
                                       │ Extract user_id
                                       ▼
┌──────────┐     {data: ...}      ┌──────────┐
│  Client  │ ←──────────────────  │  Server  │
└──────────┘                      └──────────┘
```

### JWT Implementation

```python
# core/security.py
from datetime import datetime, timedelta, UTC
from jose import jwt, JWTError
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token settings
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"


def create_access_token(user_id: UUID) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": expire,
        "iat": datetime.now(UTC)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: UUID) -> str:
    expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(UTC)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str, expected_type: str = "access") -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != expected_type:
            raise InvalidTokenError("Invalid token type")

        return payload

    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except JWTError:
        raise InvalidTokenError("Invalid token")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

### Protected Route Dependency

```python
# dependencies/auth.py
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency that validates JWT and returns current user"""

    try:
        payload = verify_token(token, expected_type="access")
        user_id = UUID(payload["sub"])
    except (InvalidTokenError, TokenExpiredError) as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = await user_service.get_by_id(db, user_id)

    if not user:
        raise HTTPException(401, "User not found")

    if not user.is_active:
        raise HTTPException(401, "User is deactivated")

    return user


async def get_current_superuser(
    user: User = Depends(get_current_user)
) -> User:
    """Dependency that requires superuser privileges"""
    if not user.is_superuser:
        raise HTTPException(403, "Superuser access required")
    return user
```

### Login Endpoint

```python
# routes/auth.py
@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> BaseResponse[TokenResponse]:
    ctx = get_context()

    # Find user by email
    user = await user_service.get_by_email(db, form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        # Log failed attempt for security monitoring
        await audit_log.log_action(db, None, "login_failed", metadata={
            "email": form_data.username,
            "reason": "invalid_credentials"
        })
        raise HTTPException(401, "Invalid email or password")

    if not user.is_active:
        raise HTTPException(401, "Account is deactivated")

    # Generate tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Update last login
    user.last_login = datetime.now(UTC)
    await db.commit()

    # Log successful login
    await audit_log.log_action(db, user.id, "login_success")

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    )
```

---

## 🚦 Rate Limiting: "Protecting the API"

### Why Rate Limiting?

```
Without rate limiting:
- Attacker sends 10,000 login attempts/minute → Brute force attack
- User sends 1000 LLM requests/minute → $$$$ bill
- Bot scrapes all documents → Resource exhaustion
```

### Implementation with slowapi

```python
# core/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

# Use user ID if authenticated, IP if not
def get_rate_limit_key(request: Request) -> str:
    # Try to get user from JWT
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            payload = verify_token(token)
            return f"user:{payload['sub']}"
        except:
            pass

    # Fallback to IP
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=get_rate_limit_key)
```

### Applying Rate Limits

```python
# routes/auth.py
@router.post("/login")
@limiter.limit("5/minute")  # Prevent brute force
async def login(...):
    ...

@router.post("/register")
@limiter.limit("3/minute")  # Prevent spam accounts
async def register(...):
    ...


# routes/chat.py
@router.post("/stream")
@limiter.limit("30/minute")  # LLM calls are expensive
async def stream_chat(...):
    ...


# routes/documents.py
@router.post("/")
@limiter.limit("10/minute")  # Prevent upload spam
async def upload_document(...):
    ...
```

### Rate Limit Headers

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 25
X-RateLimit-Reset: 1703234567

HTTP/1.1 429 Too Many Requests
Retry-After: 60
{
  "trace_id": "...",
  "error": "Rate limit exceeded. Try again in 60 seconds."
}
```

---

## 🛡️ Security Measures: "Defense in Depth"

### 1. Input Validation with Pydantic

```python
# schemas/document.py
from pydantic import BaseModel, Field, field_validator

class DocumentCreate(BaseModel):
    description: str = Field(max_length=1000)
    tags: list[str] = Field(default=[], max_items=10)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        for tag in v:
            if len(tag) > 50:
                raise ValueError("Tag too long (max 50 chars)")
            if not tag.isalnum():
                raise ValueError("Tags must be alphanumeric")
        return v


# Automatic validation
@router.post("/documents")
async def create_document(
    data: DocumentCreate,  # Pydantic validates automatically
    ...
):
    ...
```

### 2. SQL Injection Prevention

```python
# ❌ NEVER do this
query = f"SELECT * FROM users WHERE email = '{email}'"  # SQL injection!

# ✅ Always use parameterized queries (SQLAlchemy does this)
result = await db.execute(
    select(User).where(User.email == email)  # Safe!
)

# ✅ Or explicit parameters
result = await db.execute(
    text("SELECT * FROM users WHERE email = :email"),
    {"email": email}
)
```

### 3. CORS Configuration

```python
# main.py
from fastapi.middleware.cors import CORSMiddleware

# In production, specify exact origins
ALLOWED_ORIGINS = [
    "https://app.example.com",
    "https://www.example.com",
]

# In development
if settings.DEBUG:
    ALLOWED_ORIGINS.append("http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### 4. Secret Key Validation

```python
# core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        if v == "your-secret-key-here":
            raise ValueError("Please change the default SECRET_KEY")
        return v
```

### 5. Password Requirements

```python
# schemas/auth.py
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        return v
```

---

## 📝 Audit Logging: "Who Did What When"

### What to Log

```python
# Critical actions to audit
AUDITED_ACTIONS = [
    # Authentication
    "login_success",
    "login_failed",
    "logout",
    "password_change",

    # Documents
    "document_upload",
    "document_delete",

    # Agents
    "agent_create",
    "agent_update",
    "agent_delete",

    # Admin actions
    "user_deactivate",
    "user_tier_change",
    "subscription_modify",
]
```

### Logging Implementation

```python
# services/audit_log.py
async def log_action(
    db: AsyncSession,
    user_id: UUID | None,
    action: str,
    resource_type: str | None = None,
    resource_id: UUID | None = None,
    metadata: dict | None = None,
    request: Request | None = None
):
    """Log an auditable action"""

    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata=metadata or {},
        ip_address=_get_client_ip(request) if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )

    db.add(audit_log)
    await db.flush()

    # Also log to structured logging for SIEM integration
    logger.info(
        "audit_event",
        extra={
            "user_id": str(user_id),
            "action": action,
            "resource_type": resource_type,
            "resource_id": str(resource_id) if resource_id else None,
            "metadata": metadata,
        }
    )


def _get_client_ip(request: Request) -> str:
    """Get real client IP, handling proxies"""
    # Check X-Forwarded-For header (reverse proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Direct connection
    return request.client.host if request.client else "unknown"
```

### Usage in Routes

```python
@router.delete("/documents/{id}")
async def delete_document(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    request: Request = None
):
    document = await document_service.get_by_id(db, id, user.id)

    if not document:
        raise HTTPException(404, "Document not found")

    await document_service.delete(db, document)

    # Audit log
    await audit_log.log_action(
        db=db,
        user_id=user.id,
        action="document_delete",
        resource_type="document",
        resource_id=id,
        metadata={"filename": document.filename},
        request=request
    )

    return BaseResponse(trace_id=get_trace_id(), data={"deleted": True})
```

### Querying Audit Logs

```python
# Admin endpoint
@router.get("/audit-logs")
async def get_audit_logs(
    user_id: UUID | None = None,
    action: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_superuser)
):
    query = select(AuditLog).order_by(AuditLog.created_at.desc())

    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
    if from_date:
        query = query.where(AuditLog.created_at >= from_date)
    if to_date:
        query = query.where(AuditLog.created_at <= to_date)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)

    return BaseResponse(
        trace_id=get_trace_id(),
        data=[AuditLogResponse.model_validate(log) for log in result.scalars()]
    )
```

---

## 🔄 Request Context & Tracing

### TraceContextMiddleware

```python
# middleware/trace.py
from contextvars import ContextVar
from uuid import uuid4

_request_context: ContextVar[RequestContext] = ContextVar("request_context")


class RequestContext:
    def __init__(self, trace_id: str):
        self.trace_id = trace_id
        self.start_time = time.time()


class TraceContextMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Generate or extract trace ID
        headers = dict(scope.get("headers", []))
        trace_id = headers.get(b"x-trace-id", b"").decode() or str(uuid4())

        # Set context for this request
        ctx = RequestContext(trace_id=trace_id)
        token = _request_context.set(ctx)

        try:
            # Add trace_id to response headers
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.append((b"x-trace-id", trace_id.encode()))
                    message["headers"] = headers
                await send(message)

            await self.app(scope, receive, send_wrapper)
        finally:
            _request_context.reset(token)


def get_context() -> RequestContext:
    ctx = _request_context.get(None)
    if ctx is None:
        raise RuntimeError("No request context available")
    return ctx


def get_trace_id() -> str:
    return get_context().trace_id
```

### Using Trace ID for Debugging

```python
# In any service
logger.info(
    "Processing document",
    extra={
        "trace_id": get_trace_id(),
        "document_id": str(document.id),
        "user_id": str(user.id)
    }
)

# In response
return BaseResponse(
    trace_id=get_trace_id(),  # Client can report this for debugging
    data=...
)
```

---

## 📊 Error Handling

### Custom Exception Classes

```python
# core/exceptions.py
class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


class NotFoundError(AppException):
    def __init__(self, resource: str):
        super().__init__(f"{resource} not found", status_code=404)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=403)


class RateLimitError(AppException):
    def __init__(self, retry_after: int):
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s", status_code=429)
        self.retry_after = retry_after
```

### Global Exception Handler

```python
# main.py
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "trace_id": get_trace_id(),
            "data": None,
            "error": exc.message
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append(f"{field}: {error['msg']}")

    return JSONResponse(
        status_code=422,
        content={
            "trace_id": get_trace_id(),
            "data": None,
            "error": "Validation error: " + "; ".join(errors)
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log the full error for debugging
    logger.exception("Unhandled exception", extra={"trace_id": get_trace_id()})

    # Return generic error to client (don't leak internals)
    return JSONResponse(
        status_code=500,
        content={
            "trace_id": get_trace_id(),
            "data": None,
            "error": "Internal server error"
        }
    )
```

---

## 🎯 Key Takeaways

| Topic | Implementation |
|-------|----------------|
| **Response Format** | BaseResponse wrapper with trace_id |
| **Authentication** | JWT access (30min) + refresh (7 days) |
| **Rate Limiting** | slowapi, per-user/IP, endpoint-specific |
| **Input Validation** | Pydantic models with custom validators |
| **SQL Injection** | SQLAlchemy parameterized queries |
| **CORS** | Whitelist specific origins |
| **Audit Logging** | All critical actions logged |
| **Tracing** | Request context with trace_id |
| **Error Handling** | Custom exceptions + global handlers |

---

*ต่อไป: [06-challenges.md](./06-challenges.md) — Real problems encountered and how they were solved*
