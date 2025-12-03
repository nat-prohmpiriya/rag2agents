"""Agent schemas for API requests and responses."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AgentTool(str, Enum):
    """Available tools for agents."""

    rag_search = "rag_search"
    summarize = "summarize"
    calculator = "calculator"
    web_search = "web_search"


class ToolInfo(BaseModel):
    """Tool information schema."""

    name: AgentTool
    enabled: bool = True
    config: dict | None = None

    model_config = ConfigDict(from_attributes=True)


class AgentInfo(BaseModel):
    """Agent information response schema."""

    id: uuid.UUID
    user_id: uuid.UUID | None = None
    name: str
    slug: str
    description: str | None = None
    icon: str | None = None
    system_prompt: str | None = None
    tools: list[str] | None = None
    config: dict | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentCreate(BaseModel):
    """Schema for creating a new agent."""

    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(default=None, max_length=1000)
    icon: str | None = Field(default=None, max_length=50)
    system_prompt: str | None = Field(default=None, max_length=10000)
    tools: list[AgentTool] | None = Field(default=None)
    config: dict | None = Field(default=None)
    is_active: bool = True

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Research Assistant",
                "slug": "research-assistant",
                "description": "An AI assistant that helps with research tasks",
                "icon": "search",
                "system_prompt": "You are a helpful research assistant...",
                "tools": ["rag_search", "web_search"],
                "config": {"temperature": 0.7},
                "is_active": True,
            }
        }
    )


class AgentUpdate(BaseModel):
    """Schema for updating an agent."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    slug: str | None = Field(default=None, min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(default=None, max_length=1000)
    icon: str | None = Field(default=None, max_length=50)
    system_prompt: str | None = Field(default=None, max_length=10000)
    tools: list[AgentTool] | None = Field(default=None)
    config: dict | None = Field(default=None)
    is_active: bool | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Research Assistant",
                "description": "An updated description",
            }
        }
    )


class AgentListResponse(BaseModel):
    """Response schema for listing agents."""

    agents: list[AgentInfo]
    total: int
    page: int = 1
    page_size: int = 20

    model_config = ConfigDict(from_attributes=True)
