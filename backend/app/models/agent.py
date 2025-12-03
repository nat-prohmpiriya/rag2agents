"""Agent model for customizable AI agents."""

import uuid
from enum import Enum

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class AgentTool(str, Enum):
    """Available tools for agents."""

    rag_search = "rag_search"
    summarize = "summarize"
    calculator = "calculator"
    web_search = "web_search"


class AgentSource(str, Enum):
    """Source type for agents."""

    system = "system"  # Pre-built from YAML configs
    user = "user"  # Created by users


class Agent(Base, TimestampMixin):
    """Agent model for customizable AI assistants."""

    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    tools: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source: Mapped[str] = mapped_column(
        String(20),
        default=AgentSource.user.value,
        nullable=False,
        index=True,
    )
    document_ids: Mapped[list[str] | None] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        nullable=True,
        default=list,
    )

    # Relationships
    user: Mapped["User | None"] = relationship(back_populates="agents")
    project: Mapped["Project | None"] = relationship(back_populates="agents")

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name={self.name}, slug={self.slug})>"


# Import at the end to avoid circular imports
from app.models.user import User  # noqa: E402, F401
from app.models.project import Project  # noqa: E402, F401
