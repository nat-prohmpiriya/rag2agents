"""Document model for file storage and processing."""

import uuid
from enum import Enum

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class DocumentStatus(str, Enum):
    """Document processing status."""

    pending = "pending"
    processing = "processing"
    ready = "ready"
    error = "error"


class Document(Base, TimestampMixin):
    """Document model for storing uploaded files."""

    __tablename__ = "documents"

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
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # pdf, docx, txt, md, csv
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)  # bytes
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)  # storage path
    status: Mapped[DocumentStatus] = mapped_column(
        String(20),
        default=DocumentStatus.pending,
        nullable=False,
        index=True,
    )
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String(50)), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunk.chunk_index",
    )
    project_documents: Mapped[list["ProjectDocument"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"


# Import at the end to avoid circular imports
from app.models.chunk import DocumentChunk  # noqa: E402, F401
from app.models.project_document import ProjectDocument  # noqa: E402, F401
from app.models.user import User  # noqa: E402, F401
