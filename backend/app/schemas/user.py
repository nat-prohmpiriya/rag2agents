from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    username: str
    password: str
    first_name: str | None = None
    last_name: str | None = None


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    first_name: str | None = None
    last_name: str | None = None


class UserResponse(BaseModel):
    """Schema for user response."""

    id: int
    email: str
    username: str
    first_name: str | None
    last_name: str | None
    is_active: bool
    tier: str

    model_config = {"from_attributes": True}
