"""Generated image model for AI image generation history."""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class GeneratedImage(Base, TimestampMixin):
    """Model for storing generated images history."""

    __tablename__ = "generated_images"

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
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    revised_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    size: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., "1024x1024"
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)  # MinIO URL
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)  # bytes

    # Relationships
    user: Mapped["User"] = relationship(back_populates="generated_images")

    def __repr__(self) -> str:
        return f"<GeneratedImage(id={self.id}, prompt={self.prompt[:50]}..., model={self.model})>"


# Import at the end to avoid circular imports
from app.models.user import User  # noqa: E402, F401
