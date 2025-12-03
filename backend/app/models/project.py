"""Project model for organizing user workspaces."""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class PrivacyLevel(str, enum.Enum):
    """Privacy level for PII protection."""

    STRICT = "strict"
    MODERATE = "moderate"
    OFF = "off"


class Project(Base, TimestampMixin):
    """Project model for organizing documents and conversations."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    privacy_level: Mapped[PrivacyLevel] = mapped_column(
        Enum(PrivacyLevel),
        default=PrivacyLevel.MODERATE,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="projects")
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    project_documents: Mapped[list["ProjectDocument"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    agents: Mapped[list["Agent"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name})>"


# Import at the end to avoid circular imports
from app.models.user import User  # noqa: E402, F401
from app.models.conversation import Conversation  # noqa: E402, F401
from app.models.project_document import ProjectDocument  # noqa: E402, F401
from app.models.agent import Agent  # noqa: E402, F401
