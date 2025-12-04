"""Admin dashboard and user management schemas."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class UserStats(BaseModel):
    """User statistics."""

    total_users: int
    active_today: int
    new_this_week: int
    new_this_month: int


class UsageStats(BaseModel):
    """Usage statistics from LiteLLM."""

    requests_today: int
    requests_this_month: int
    tokens_today: int
    tokens_this_month: int
    cost_today: float
    cost_this_month: float


class RevenueStats(BaseModel):
    """Revenue statistics."""

    mrr: float  # Monthly Recurring Revenue
    arr: float  # Annual Recurring Revenue
    total_revenue: float
    revenue_this_month: float


class PlanSubscriberCount(BaseModel):
    """Subscriber count per plan."""

    plan_id: str
    plan_name: str
    display_name: str
    subscriber_count: int
    percentage: float

    model_config = ConfigDict(from_attributes=True)


class DailyUsage(BaseModel):
    """Daily usage data point for charts."""

    date: str  # ISO date string
    requests: int
    tokens: int
    cost: float


class DashboardStats(BaseModel):
    """Complete dashboard statistics."""

    users: UserStats
    usage: UsageStats
    revenue: RevenueStats
    subscribers_by_plan: list[PlanSubscriberCount]
    usage_over_time: list[DailyUsage]


# User management schemas
class UserStatus(str, Enum):
    """User status enumeration for filtering."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BANNED = "banned"


class AdminUserResponse(BaseModel):
    """User response for admin panel with extended info."""

    id: uuid.UUID
    email: str
    username: str
    first_name: str | None
    last_name: str | None
    is_active: bool
    is_superuser: bool
    tier: str
    status: str
    plan_name: str | None
    subscription_status: str | None
    tokens_used: int
    tokens_limit: int
    revenue_total: float
    last_active: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminUserListResponse(BaseModel):
    """Paginated user list response."""

    items: list[AdminUserResponse]
    total: int
    page: int
    per_page: int
    pages: int


class AdminUserUpdate(BaseModel):
    """Schema for admin updating a user."""

    first_name: str | None = None
    last_name: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    tier: str | None = None


class BulkUserAction(BaseModel):
    """Schema for bulk user actions."""

    user_ids: list[uuid.UUID]
    action: str  # change_plan, suspend, activate, ban
    plan_id: uuid.UUID | None = None  # Required for change_plan


class UserActionResult(BaseModel):
    """Result of user action."""

    success: bool
    user_id: uuid.UUID
    message: str


class BulkActionResponse(BaseModel):
    """Response for bulk user actions."""

    results: list[UserActionResult]
    success_count: int
    failure_count: int


class ChangeUserPlanRequest(BaseModel):
    """Request to change user's plan."""

    plan_id: uuid.UUID


class SuspendUserRequest(BaseModel):
    """Request to suspend a user."""

    reason: str | None = None
