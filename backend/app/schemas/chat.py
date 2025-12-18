"""Chat request and response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImageData(BaseModel):
    """Image data for vision/multimodal requests."""

    media_type: str = Field(..., description="MIME type of the image (e.g., image/png, image/jpeg)")
    data: str = Field(..., description="Base64 encoded image data")


class ChatRequest(BaseModel):
    """Chat request schema."""

    message: str = Field(..., min_length=1, max_length=32000)
    conversation_id: uuid.UUID | None = None
    model: str | None = None  # Override default model
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=128000)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=0.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=0.0, le=2.0)
    stream: bool = False
    use_rag: bool = Field(default=False, description="Enable RAG to use uploaded documents")
    rag_top_k: int = Field(default=5, ge=1, le=20, description="Number of document chunks to retrieve")
    rag_document_ids: list[uuid.UUID] | None = Field(
        default=None,
        description="Optional list of document IDs to scope RAG search. If None, search all user's documents."
    )
    project_id: uuid.UUID | None = Field(
        default=None,
        description="Optional project ID to scope RAG search to documents in that project."
    )
    agent_slug: str | None = Field(
        default=None,
        description="Optional agent slug to use for processing. If provided, uses AgentEngine with tools."
    )
    skip_user_save: bool = Field(
        default=False,
        description="Skip saving user message to DB (used for regenerate response)"
    )
    thinking: bool = Field(
        default=False,
        description="Enable extended thinking mode for supported models (e.g., Gemini 2.5)"
    )
    web_search: bool = Field(
        default=False,
        description="Enable web search tool for grounding responses with real-time information"
    )
    images: list[ImageData] | None = Field(
        default=None,
        description="Optional list of images for vision/multimodal models"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Hello, how are you?",
                "conversation_id": "conv_123",
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "stream": False,
                "use_rag": False,
                "rag_top_k": 5,
                "rag_document_ids": None,
                "project_id": None,
                "agent_slug": None,
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


class LatencyInfo(BaseModel):
    """Latency information for chat responses."""

    retrieval_ms: int | None = None
    llm_ms: int | None = None


class SourceInfo(BaseModel):
    """Source document information for RAG responses."""

    document_id: str
    filename: str
    chunk_index: int
    score: float = Field(description="Similarity score (0-1, higher is better)")
    content: str = Field(description="Chunk content preview")

    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    """Chat response schema (non-streaming)."""

    message: ChatMessage
    model: str
    usage: UsageInfo | None = None
    conversation_id: uuid.UUID | None = None
    sources: list[SourceInfo] | None = None

    model_config = ConfigDict(from_attributes=True)


class ChatStreamChunk(BaseModel):
    """Single chunk in streaming response."""

    content: str
    done: bool = False


class AgentChatResponse(BaseModel):
    """Chat response when using an agent."""

    message: ChatMessage
    model: str | None = None
    usage: UsageInfo | None = None
    conversation_id: uuid.UUID | None = None
    sources: list[SourceInfo] | None = None
    tools_used: list[str] | None = None
    thinking: str | None = None
    agent_slug: str | None = None

    model_config = ConfigDict(from_attributes=True)
