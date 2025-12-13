from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import get_context
from app.core.dependencies import get_current_user, get_db
from app.core.rate_limit import RateLimits, limiter
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse
from app.schemas.base import BaseResponse, MessageResponse
from app.schemas.user import UserCreate, UserResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
@limiter.limit(RateLimits.AUTH_REGISTER)
async def register(
    request: Request,
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse[UserResponse]:
    """Register a new user."""
    ctx = get_context()
    user = await auth_service.register_user(db, data)
    return BaseResponse(
        trace_id=ctx.trace_id,
        data=UserResponse.model_validate(user),
    )


@router.post("/login")
@limiter.limit(RateLimits.AUTH_LOGIN)
async def login(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse[TokenResponse]:
    """Login and get access/refresh tokens."""
    ctx = get_context()
    user = await auth_service.authenticate_user(db, data.email, data.password)
    tokens = auth_service.create_tokens(user.id)
    return BaseResponse(
        trace_id=ctx.trace_id,
        data=tokens,
    )


@router.post("/refresh")
@limiter.limit(RateLimits.AUTH_REFRESH)
async def refresh_token(
    request: Request,
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse[TokenResponse]:
    """Refresh access token using refresh token."""
    ctx = get_context()
    tokens = await auth_service.refresh_access_token(db, data.refresh_token)
    return BaseResponse(
        trace_id=ctx.trace_id,
        data=tokens,
    )


@router.post("/logout")
async def logout() -> BaseResponse[MessageResponse]:
    """
    Logout endpoint.

    Note: With JWT, logout is typically handled client-side by removing the token.
    This endpoint exists for API completeness and can be extended
    to implement token blacklisting if needed.
    """
    ctx = get_context()
    return BaseResponse(
        trace_id=ctx.trace_id,
        data=MessageResponse(message="Successfully logged out"),
    )


@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
) -> BaseResponse[UserResponse]:
    """Get current authenticated user."""
    ctx = get_context()
    return BaseResponse(
        trace_id=ctx.trace_id,
        data=UserResponse.model_validate(current_user),
    )
