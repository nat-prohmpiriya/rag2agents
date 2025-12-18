"""Usage schemas for API request/response."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.usage import RequestType


class UsageRecordCreate(BaseModel):
    """Schema for creating a usage record."""

    request_type: RequestType = RequestType.CHAT
    model: str = Field(..., min_length=1, max_length=100)
    tokens_input: int = Field(0, ge=0)
    tokens_output: int = Field(0, ge=0)
    tokens_total: int = Field(0, ge=0)
    cost: float = Field(0.0, ge=0)
    credits_used: int = Field(1, ge=1)
    latency_ms: int | None = None
    conversation_id: uuid.UUID | None = None
    message_id: uuid.UUID | None = None
    agent_id: uuid.UUID | None = None
    litellm_call_id: str | None = None
    extra_data: dict | None = None


class UsageRecordResponse(BaseModel):
    """Schema for usage record response."""

    id: uuid.UUID
    user_id: uuid.UUID
    request_type: RequestType
    model: str
    tokens_input: int
    tokens_output: int
    tokens_total: int
    cost: float
    credits_used: int
    latency_ms: int | None
    conversation_id: uuid.UUID | None
    message_id: uuid.UUID | None
    agent_id: uuid.UUID | None
    litellm_call_id: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UsageSummaryResponse(BaseModel):
    """Schema for usage summary response."""

    id: uuid.UUID
    user_id: uuid.UUID
    period: str
    total_requests: int
    total_tokens: int
    total_credits: int
    total_cost: float
    chat_requests: int
    rag_requests: int
    agent_requests: int
    embedding_requests: int
    last_synced_at: datetime | None
    is_synced: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UsageStatsResponse(BaseModel):
    """Schema for user's current usage statistics."""

    # Current period
    period: str

    # Usage counts
    requests_used: int
    requests_limit: int
    requests_remaining: int
    requests_percentage: float

    credits_used: int
    credits_limit: int
    credits_remaining: int
    credits_percentage: float

    tokens_used: int
    tokens_limit: int
    tokens_remaining: int
    tokens_percentage: float

    # Cost
    total_cost: float

    # Breakdown
    by_request_type: dict[str, int]
    by_model: dict[str, int]

    # Status flags
    is_requests_exceeded: bool
    is_credits_exceeded: bool
    is_tokens_exceeded: bool
    is_warning: bool  # 80% threshold


class CreditConfig(BaseModel):
    """Configuration for credit calculation per model."""

    model: str
    credits_per_request: int = 1
    description: str | None = None


class CreditConfigResponse(BaseModel):
    """Response with credit configurations."""

    configs: list[CreditConfig]
    default_credits: int = 1


# Default credit configuration
DEFAULT_CREDIT_CONFIG: dict[str, int] = {
    # OpenAI models
    "gpt-3.5-turbo": 1,
    "gpt-4o-mini": 1,
    "gpt-4o": 3,
    "gpt-4-turbo": 5,
    "gpt-4": 5,
    # Anthropic models
    "claude-3-haiku": 1,
    "claude-3-sonnet": 2,
    "claude-3-opus": 5,
    "claude-3.5-sonnet": 3,
    # Google Gemini models
    "gemini-1.5-flash": 1,
    "gemini-1.5-pro": 3,
    "gemini-2.0-flash": 1,
    "gemini-2.5-flash": 1,
    "gemini-2.5-flash-lite": 1,
    "gemini-2.5-pro": 3,
    "gemini-3-flash": 2,
    "gemini-3-pro": 4,
}


def get_credits_for_model(model: str) -> int:
    """Get credit cost for a model.

    Args:
        model: Model name (can be full path like openai/gpt-4o)

    Returns:
        Number of credits for this model
    """
    # Extract base model name from full path
    base_model = model.split("/")[-1] if "/" in model else model

    # Try exact match first
    if base_model in DEFAULT_CREDIT_CONFIG:
        return DEFAULT_CREDIT_CONFIG[base_model]

    # Try partial match
    for key, credits in DEFAULT_CREDIT_CONFIG.items():
        if key in base_model.lower() or base_model.lower() in key:
            return credits

    # Default to 1 credit
    return 1
