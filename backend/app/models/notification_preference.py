"""Notification preference model for user notification settings."""

import uuid
from datetime import time

from sqlalchemy import Boolean, ForeignKey, Time
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin

# Default category settings
DEFAULT_CATEGORY_SETTINGS = {
    "billing": {"email": True, "in_app": True},
    "document": {"email": False, "in_app": True},
    "system": {"email": True, "in_app": True},
    "account": {"email": True, "in_app": True},
}


class NotificationPreference(Base, TimestampMixin):
    """Notification preference model for user notification settings."""

    __tablename__ = "notification_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # User (one preference per user)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Global toggles
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Per-category settings (JSONB for flexibility)
    category_settings: Mapped[dict] = mapped_column(
        JSONB, default=DEFAULT_CATEGORY_SETTINGS, nullable=False
    )

    # Quiet hours (optional)
    quiet_hours_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    quiet_hours_end: Mapped[time | None] = mapped_column(Time, nullable=True)

    def __repr__(self) -> str:
        return f"<NotificationPreference(id={self.id}, user_id={self.user_id})>"
