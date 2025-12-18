"""Workflow models for visual workflow builder."""

import uuid
from enum import Enum

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


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


class Workflow(Base, TimestampMixin):
    """Workflow model for storing visual workflow definitions."""

    __tablename__ = "workflows"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Visual flow data (nodes and edges from Svelte Flow)
    nodes: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    edges: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)

    # Viewport state (zoom, position)
    viewport: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)

    # Workflow settings
    status: Mapped[str] = mapped_column(
        String(20),
        default=WorkflowStatus.draft.value,
        nullable=False,
        index=True,
    )
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="workflows")
    executions: Mapped[list["WorkflowExecution"]] = relationship(
        back_populates="workflow",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Workflow(id={self.id}, name={self.name}, status={self.status})>"


class WorkflowExecution(Base, TimestampMixin):
    """Workflow execution history and state."""

    __tablename__ = "workflow_executions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Execution state
    status: Mapped[str] = mapped_column(
        String(20),
        default=ExecutionStatus.pending.value,
        nullable=False,
        index=True,
    )

    # Input/Output data
    inputs: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    outputs: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)

    # Execution details
    node_states: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    current_node_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Execution logs (step-by-step)
    logs: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)

    # Timing
    started_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Token usage
    total_tokens: Mapped[int | None] = mapped_column(default=0)

    # Relationships
    workflow: Mapped["Workflow"] = relationship(back_populates="executions")
    user: Mapped["User"] = relationship(back_populates="workflow_executions")

    def __repr__(self) -> str:
        return f"<WorkflowExecution(id={self.id}, workflow_id={self.workflow_id}, status={self.status})>"


# Import at the end to avoid circular imports
from app.models.user import User  # noqa: E402, F401
