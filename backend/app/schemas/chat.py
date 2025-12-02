"""Chat request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """Chat request schema."""

    message: str = Field(..., min_length=1, max_length=32000)
    conversation_id: str | None = None
    model: str | None = None  # Override default model
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=128000)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=0.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=0.0, le=2.0)
    stream: bool = False

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Hello, how are you?",
                "conversation_id": "conv_123",
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "stream": False,
            }
        }
    )


class ChatMessage(BaseModel):
    """Chat message in response."""

    role: str  # user, assistant, system
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


class UsageInfo(BaseModel):
    """Token usage information from LLM response."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    model_config = ConfigDict(extra="ignore")


class ChatResponse(BaseModel):
    """Chat response schema (non-streaming)."""

    message: ChatMessage
    model: str
    usage: UsageInfo | None = None
    conversation_id: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ChatStreamChunk(BaseModel):
    """Single chunk in streaming response."""

    content: str
    done: bool = False
