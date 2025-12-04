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


# User Detail schemas
class UserSubscriptionDetail(BaseModel):
    """Subscription detail for user detail page."""

    id: uuid.UUID
    plan_name: str
    plan_display_name: str
    status: str
    billing_interval: str
    price: float
    start_date: datetime
    current_period_start: datetime | None
    current_period_end: datetime | None
    trial_end_date: datetime | None
    canceled_at: datetime | None
    cancel_reason: str | None

    model_config = ConfigDict(from_attributes=True)


class UserUsageDetail(BaseModel):
    """Usage statistics for user detail page."""

    tokens_used_today: int
    tokens_used_this_month: int
    tokens_limit: int
    requests_today: int
    requests_this_month: int
    cost_today: float
    cost_this_month: float


class UserUsageHistory(BaseModel):
    """Daily usage history for charts."""

    date: str
    tokens: int
    requests: int
    cost: float


class UserConversationSummary(BaseModel):
    """Conversation summary for user detail page."""

    id: uuid.UUID
    title: str | None
    message_count: int
    last_message_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserDocumentSummary(BaseModel):
    """Document summary for user detail page."""

    id: uuid.UUID
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserActivityLog(BaseModel):
    """Activity log entry for user detail page."""

    id: uuid.UUID
    action: str
    description: str
    metadata: dict | None
    created_at: datetime


class UserInvoiceSummary(BaseModel):
    """Invoice summary for user detail page."""

    id: uuid.UUID
    invoice_number: str
    status: str
    total: float
    amount_paid: float
    currency: str
    invoice_date: datetime
    paid_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class UserDetailResponse(BaseModel):
    """Complete user detail response."""

    # Basic info
    id: uuid.UUID
    email: str
    username: str
    first_name: str | None
    last_name: str | None
    is_active: bool
    is_superuser: bool
    tier: str
    created_at: datetime
    updated_at: datetime

    # Subscription & billing
    active_subscription: UserSubscriptionDetail | None
    subscription_history: list[UserSubscriptionDetail]

    # Usage stats
    usage: UserUsageDetail
    usage_history: list[UserUsageHistory]

    # Content counts
    total_conversations: int
    total_documents: int
    total_projects: int

    # Revenue
    total_revenue: float
    invoices: list[UserInvoiceSummary]

    # Recent activity
    recent_conversations: list[UserConversationSummary]
    recent_documents: list[UserDocumentSummary]

    model_config = ConfigDict(from_attributes=True)


# Usage Analytics schemas
class UsageSummary(BaseModel):
    """Summary of usage statistics."""

    total_requests: int
    total_tokens: int
    total_cost: float
    requests_today: int
    tokens_today: int
    cost_today: float
    period_days: int


class UserSpend(BaseModel):
    """User spend data from LiteLLM."""

    user_id: str | None
    user_email: str | None
    total_spend: float
    total_requests: int
    total_tokens: int


class ModelUsage(BaseModel):
    """Usage aggregated by model."""

    model: str
    requests: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float


class DailyUsageData(BaseModel):
    """Daily usage data for charts."""

    date: str
    requests: int
    tokens: int
    cost: float


class PlanUsage(BaseModel):
    """Usage aggregated by plan."""

    plan_id: str
    plan_name: str
    users_count: int
    total_requests: int
    total_tokens: int
    total_cost: float
    revenue: float
    profit_margin: float


class UsageAnalyticsResponse(BaseModel):
    """Complete usage analytics response."""

    summary: UsageSummary
    by_user: list[dict]  # Flexible structure from LiteLLM
    by_model: list[ModelUsage]
    by_date: list[DailyUsageData]
    by_plan: list[PlanUsage] = []


# System Health schemas
class ServiceStatus(str, Enum):
    """Service health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class LiteLLMHealth(BaseModel):
    """LiteLLM Proxy health status."""

    status: ServiceStatus
    url: str
    response_time_ms: float | None = None
    models_available: int = 0
    error: str | None = None


class PostgreSQLHealth(BaseModel):
    """PostgreSQL database health status."""

    status: ServiceStatus
    host: str
    active_connections: int = 0
    max_connections: int = 0
    database_size_mb: float = 0
    response_time_ms: float | None = None
    error: str | None = None


class RedisHealth(BaseModel):
    """Redis health status."""

    status: ServiceStatus
    host: str
    port: int
    used_memory_mb: float = 0
    max_memory_mb: float = 0
    connected_clients: int = 0
    hit_rate: float = 0
    response_time_ms: float | None = None
    error: str | None = None


class SystemHealthResponse(BaseModel):
    """Complete system health status."""

    overall_status: ServiceStatus
    timestamp: datetime
    litellm: LiteLLMHealth
    postgresql: PostgreSQLHealth
    redis: RedisHealth


class AlertThreshold(BaseModel):
    """Alert threshold configuration."""

    name: str
    description: str
    current_value: float | None = None
    warning_threshold: float
    critical_threshold: float
    unit: str
    enabled: bool = True


class AlertConfig(BaseModel):
    """Alert configuration."""

    latency_warning_ms: float = 500
    latency_critical_ms: float = 2000
    error_rate_warning_percent: float = 1.0
    error_rate_critical_percent: float = 5.0
    notification_channels: list[str] = []


class SystemMetrics(BaseModel):
    """System performance metrics."""

    requests_per_second: float = 0
    avg_response_time_ms: float = 0
    error_rate_percent: float = 0
    active_users: int = 0
    uptime_seconds: float = 0


# Audit Log schemas
class AuditActionType(str, Enum):
    """Audit action type enumeration."""

    # User actions
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_SUSPEND = "user_suspend"
    USER_ACTIVATE = "user_activate"
    USER_BAN = "user_ban"

    # Plan actions
    PLAN_CREATE = "plan_create"
    PLAN_UPDATE = "plan_update"
    PLAN_DELETE = "plan_delete"

    # Subscription actions
    SUBSCRIPTION_CREATE = "subscription_create"
    SUBSCRIPTION_UPGRADE = "subscription_upgrade"
    SUBSCRIPTION_DOWNGRADE = "subscription_downgrade"
    SUBSCRIPTION_CANCEL = "subscription_cancel"

    # Billing actions
    REFUND_ISSUE = "refund_issue"
    INVOICE_VOID = "invoice_void"

    # System actions
    SETTINGS_UPDATE = "settings_update"
    SYSTEM_CONFIG = "system_config"


class AuditLogAdmin(BaseModel):
    """Admin info in audit log."""

    id: uuid.UUID
    email: str
    username: str

    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    """Single audit log entry response."""

    id: uuid.UUID
    admin_id: uuid.UUID | None
    admin: AuditLogAdmin | None
    action: str
    description: str
    target_type: str | None
    target_id: uuid.UUID | None
    details: dict | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    """Paginated audit log list response."""

    items: list[AuditLogResponse]
    total: int
    page: int
    per_page: int
    pages: int


class AuditLogCreate(BaseModel):
    """Schema for creating an audit log entry."""

    action: str
    description: str
    target_type: str | None = None
    target_id: uuid.UUID | None = None
    details: dict | None = None


class AuditLogFilter(BaseModel):
    """Filter options for audit logs."""

    action: str | None = None
    admin_id: uuid.UUID | None = None
    target_type: str | None = None
    target_id: uuid.UUID | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


# Settings schemas
class SettingCategory(str, Enum):
    """Setting category enumeration."""

    GENERAL = "general"
    PAYMENT = "payment"
    LITELLM = "litellm"
    NOTIFICATION = "notification"


class SettingResponse(BaseModel):
    """Single setting response."""

    id: uuid.UUID
    key: str
    value: str | None
    value_json: dict | None
    category: str
    description: str | None
    is_secret: bool
    is_editable: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SettingUpdate(BaseModel):
    """Schema for updating a setting."""

    value: str | None = None
    value_json: dict | None = None
    description: str | None = None


class SettingCreate(BaseModel):
    """Schema for creating a setting."""

    key: str
    value: str | None = None
    value_json: dict | None = None
    category: str = SettingCategory.GENERAL.value
    description: str | None = None
    is_secret: bool = False
    is_editable: bool = True


class SettingsByCategoryResponse(BaseModel):
    """Settings grouped by category."""

    general: list[SettingResponse] = []
    payment: list[SettingResponse] = []
    litellm: list[SettingResponse] = []
    notification: list[SettingResponse] = []


# Structured settings for frontend forms
class GeneralSettings(BaseModel):
    """General application settings."""

    site_name: str = "RAG Agent Platform"
    default_plan_id: str | None = None
    trial_period_days: int = 14
    allow_registration: bool = True
    require_email_verification: bool = True


class PaymentSettings(BaseModel):
    """Payment/Stripe settings."""

    stripe_publishable_key: str | None = None
    stripe_secret_key: str | None = None  # Will be masked on response
    stripe_webhook_secret: str | None = None  # Will be masked on response
    currency: str = "usd"
    tax_rate_percent: float = 0.0


class LiteLLMSettings(BaseModel):
    """LiteLLM proxy settings."""

    proxy_url: str | None = None
    master_key: str | None = None  # Will be masked on response
    default_model: str = "gemini-2.0-flash"
    fallback_model: str | None = None
    request_timeout_seconds: int = 60


class NotificationSettings(BaseModel):
    """Notification settings."""

    slack_webhook_url: str | None = None  # Will be masked on response
    email_enabled: bool = True
    email_from_name: str = "RAG Agent Platform"
    email_from_address: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None  # Will be masked on response
    smtp_use_tls: bool = True


class AllSettingsResponse(BaseModel):
    """All settings response for admin UI."""

    general: GeneralSettings
    payment: PaymentSettings
    litellm: LiteLLMSettings
    notification: NotificationSettings


class AllSettingsUpdate(BaseModel):
    """Update all settings at once."""

    general: GeneralSettings | None = None
    payment: PaymentSettings | None = None
    litellm: LiteLLMSettings | None = None
    notification: NotificationSettings | None = None
