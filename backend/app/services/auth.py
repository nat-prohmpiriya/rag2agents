import logging
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
from app.core.telemetry import traced
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)


@traced(skip_input=True)  # Skip input to avoid logging passwords
async def register_user(db: AsyncSession, data: UserCreate) -> User:
    """Register a new user."""
    # Check if email already exists
    stmt = select(User).where(User.email == data.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        logger.warning("Registration failed: email already exists", extra={"email": data.email})
        raise ValidationError("Email already registered")

    # Check if username already exists
    stmt = select(User).where(User.username == data.username)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        logger.warning("Registration failed: username taken", extra={"username": data.username})
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

    logger.info("User registered successfully", extra={"user_id": str(user.id), "email": data.email})
    return user


@traced(skip_input=True)  # Skip input to avoid logging passwords
async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> User:
    """Authenticate user by email and password."""
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        logger.warning("Authentication failed: user not found", extra={"email": email})
        raise InvalidCredentialsError()

    if not verify_password(password, user.hashed_password):
        logger.warning("Authentication failed: invalid password", extra={"user_id": str(user.id)})
        raise InvalidCredentialsError()

    if not user.is_active:
        logger.warning("Authentication failed: user inactive", extra={"user_id": str(user.id)})
        raise InvalidCredentialsError("User account is disabled")

    logger.info("User authenticated successfully", extra={"user_id": str(user.id)})
    return user


@traced(skip_output=True)  # Skip output to avoid logging tokens
def create_tokens(user_id: uuid.UUID) -> TokenResponse:
    """Create access and refresh tokens for a user."""
    token_data = {"sub": str(user_id)}
    logger.debug("Creating tokens", extra={"user_id": str(user_id)})
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@traced(skip_input=True, skip_output=True)  # Skip to avoid logging tokens
async def refresh_access_token(db: AsyncSession, refresh_token: str) -> TokenResponse:
    """Refresh access token using refresh token."""
    payload = decode_token(refresh_token)

    if not payload:
        logger.warning("Token refresh failed: invalid token")
        raise InvalidCredentialsError("Invalid refresh token")

    if payload.get("type") != "refresh":
        logger.warning("Token refresh failed: wrong token type")
        raise InvalidCredentialsError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        logger.warning("Token refresh failed: missing user_id")
        raise InvalidCredentialsError("Invalid refresh token")

    # Verify user still exists and is active
    stmt = select(User).where(User.id == uuid.UUID(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        logger.warning("Token refresh failed: user inactive", extra={"user_id": user_id})
        raise InvalidCredentialsError("User not found or inactive")

    logger.info("Token refreshed successfully", extra={"user_id": user_id})
    return create_tokens(user.id)


@traced()
async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Get user by ID."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


@traced()
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

    logger.info("User profile updated", extra={"user_id": str(user.id)})
    return user


@traced(skip_input=True)  # Skip input to avoid logging passwords
async def change_password(
    db: AsyncSession, user: User, current_password: str, new_password: str
) -> User:
    """Change user password after verifying current password."""
    if not verify_password(current_password, user.hashed_password):
        logger.warning("Password change failed: incorrect current password", extra={"user_id": str(user.id)})
        raise InvalidCredentialsError("Current password is incorrect")

    user.hashed_password = hash_password(new_password)
    await db.commit()
    await db.refresh(user)

    logger.info("Password changed successfully", extra={"user_id": str(user.id)})
    return user


@traced(skip_input=True)  # Skip input to avoid logging passwords
async def delete_account(db: AsyncSession, user: User, password: str) -> User:
    """Soft delete user account after verifying password."""
    if not verify_password(password, user.hashed_password):
        logger.warning("Account deletion failed: incorrect password", extra={"user_id": str(user.id)})
        raise InvalidCredentialsError("Password is incorrect")

    user.is_active = False
    await db.commit()
    await db.refresh(user)

    logger.info("Account deleted (soft)", extra={"user_id": str(user.id)})
    return user
