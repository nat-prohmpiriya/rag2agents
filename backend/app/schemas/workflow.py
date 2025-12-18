"""Workflow schemas for API requests and responses."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class NodeType(str, Enum):
    """Available node types for workflow."""

    start = "start"
    end = "end"
    llm = "llm"
    agent = "agent"
    rag = "rag"
    tool = "tool"
    condition = "condition"
    loop = "loop"
    custom_function = "custom_function"
    http = "http"


class WorkflowStatus(str, Enum):
    """Workflow status."""

    draft = "draft"
    active = "active"
    archived = "archived"


class ExecutionStatus(str, Enum):
    """Workflow execution status."""

    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


# =============================================================================
# Node Schemas (for Svelte Flow)
# =============================================================================

class NodePosition(BaseModel):
    """Node position on canvas."""

    x: float
    y: float


class NodeData(BaseModel):
    """Node data configuration."""

    label: str
    type: NodeType
    config: dict = Field(default_factory=dict)


class WorkflowNode(BaseModel):
    """Workflow node schema (Svelte Flow compatible)."""

    id: str
    type: str  # Custom node type name
    position: NodePosition
    data: NodeData
    width: float | None = None
    height: float | None = None

    model_config = ConfigDict(from_attributes=True)


class WorkflowEdge(BaseModel):
    """Workflow edge schema (Svelte Flow compatible)."""

    id: str
    source: str  # Source node ID
    target: str  # Target node ID
    sourceHandle: str | None = None  # For nodes with multiple outputs
    targetHandle: str | None = None  # For nodes with multiple inputs
    type: str | None = None  # Edge type (default, smoothstep, etc.)
    animated: bool = False
    label: str | None = None  # For condition edges (true/false)

    model_config = ConfigDict(from_attributes=True)


class Viewport(BaseModel):
    """Canvas viewport state."""

    x: float = 0
    y: float = 0
    zoom: float = 1


# =============================================================================
# Workflow CRUD Schemas
# =============================================================================

class WorkflowCreate(BaseModel):
    """Schema for creating a new workflow."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    nodes: list[WorkflowNode] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)
    viewport: Viewport | None = None
    is_template: bool = False
    config: dict | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "RAG Chat Flow",
                "description": "A simple RAG workflow",
                "nodes": [
                    {
                        "id": "start-1",
                        "type": "startNode",
                        "position": {"x": 100, "y": 100},
                        "data": {"label": "Start", "type": "start", "config": {}},
                    },
                    {
                        "id": "rag-1",
                        "type": "ragNode",
                        "position": {"x": 300, "y": 100},
                        "data": {"label": "RAG Search", "type": "rag", "config": {"top_k": 5}},
                    },
                    {
                        "id": "end-1",
                        "type": "endNode",
                        "position": {"x": 500, "y": 100},
                        "data": {"label": "End", "type": "end", "config": {}},
                    },
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "rag-1"},
                    {"id": "e2", "source": "rag-1", "target": "end-1"},
                ],
            }
        }
    )


class WorkflowUpdate(BaseModel):
    """Schema for updating a workflow."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    nodes: list[WorkflowNode] | None = None
    edges: list[WorkflowEdge] | None = None
    viewport: Viewport | None = None
    status: WorkflowStatus | None = None
    is_template: bool | None = None
    config: dict | None = None


class WorkflowInfo(BaseModel):
    """Workflow information response schema."""

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str | None = None
    nodes: list[WorkflowNode] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)
    viewport: Viewport | None = None
    status: WorkflowStatus = WorkflowStatus.draft
    is_template: bool = False
    config: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowListResponse(BaseModel):
    """Response schema for listing workflows."""

    workflows: list[WorkflowInfo]
    total: int
    page: int = 1
    page_size: int = 20


# =============================================================================
# Workflow Execution Schemas
# =============================================================================

class WorkflowExecuteRequest(BaseModel):
    """Request schema for executing a workflow."""

    inputs: dict = Field(default_factory=dict)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "inputs": {
                    "query": "What is RAG?",
                    "document_ids": ["uuid1", "uuid2"],
                }
            }
        }
    )


class NodeExecutionLog(BaseModel):
    """Log entry for a single node execution."""

    node_id: str
    node_type: str
    status: str  # pending, running, completed, failed
    started_at: str | None = None
    completed_at: str | None = None
    input: dict | None = None
    output: dict | None = None
    error: str | None = None
    tokens_used: int = 0


class WorkflowExecutionInfo(BaseModel):
    """Workflow execution information response."""

    id: uuid.UUID
    workflow_id: uuid.UUID
    user_id: uuid.UUID
    status: ExecutionStatus
    inputs: dict | None = None
    outputs: dict | None = None
    node_states: dict | None = None
    current_node_id: str | None = None
    error_message: str | None = None
    logs: list[NodeExecutionLog] = Field(default_factory=list)
    started_at: str | None = None
    completed_at: str | None = None
    total_tokens: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowExecutionListResponse(BaseModel):
    """Response schema for listing workflow executions."""

    executions: list[WorkflowExecutionInfo]
    total: int
    page: int = 1
    page_size: int = 20
