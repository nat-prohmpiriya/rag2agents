"""ProjectDocument model for many-to-many relationship between projects and documents."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProjectDocument(Base):
    """Junction table for Project-Document many-to-many relationship."""

    __tablename__ = "project_documents"
    __table_args__ = (
        UniqueConstraint("project_id", "document_id", name="uq_project_document"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="project_documents")
    document: Mapped["Document"] = relationship(back_populates="project_documents")

    def __repr__(self) -> str:
        return f"<ProjectDocument(project_id={self.project_id}, document_id={self.document_id})>"


# Import at the end to avoid circular imports
from app.models.document import Document  # noqa: E402, F401
from app.models.project import Project  # noqa: E402, F401
