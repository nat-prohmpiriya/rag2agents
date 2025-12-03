import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidCredentialsError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate


async def register_user(db: AsyncSession, data: UserCreate) -> User:
    """Register a new user."""
    # Check if email already exists
    stmt = select(User).where(User.email == data.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise ValidationError("Email already registered")

    # Check if username already exists
    stmt = select(User).where(User.username == data.username)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise ValidationError("Username already taken")

    # Create user
    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> User:
    """Authenticate user by email and password."""
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise InvalidCredentialsError()

    if not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError()

    if not user.is_active:
        raise InvalidCredentialsError("User account is disabled")

    return user


def create_tokens(user_id: uuid.UUID) -> TokenResponse:
    """Create access and refresh tokens for a user."""
    token_data = {"sub": str(user_id)}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> TokenResponse:
    """Refresh access token using refresh token."""
    payload = decode_token(refresh_token)

    if not payload:
        raise InvalidCredentialsError("Invalid refresh token")

    if payload.get("type") != "refresh":
        raise InvalidCredentialsError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise InvalidCredentialsError("Invalid refresh token")

    # Verify user still exists and is active
    stmt = select(User).where(User.id == uuid.UUID(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise InvalidCredentialsError("User not found or inactive")

    return create_tokens(user.id)


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Get user by ID."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_user_profile(
    db: AsyncSession, user: User, first_name: str | None, last_name: str | None
) -> User:
    """Update user profile."""
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name

    await db.commit()
    await db.refresh(user)
    return user
