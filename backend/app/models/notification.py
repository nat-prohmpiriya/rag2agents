"""Notification model for user notifications."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class NotificationType(str, Enum):
    """Enumeration of notification types."""

    # Billing notifications
    QUOTA_WARNING = "quota_warning"
    QUOTA_EXCEEDED = "quota_exceeded"
    SUBSCRIPTION_EXPIRING = "subscription_expiring"
    SUBSCRIPTION_RENEWED = "subscription_renewed"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_SUCCESS = "payment_success"

    # Document notifications
    DOCUMENT_PROCESSED = "document_processed"
    DOCUMENT_FAILED = "document_failed"

    # System notifications
    SYSTEM_MAINTENANCE = "system_maintenance"
    SYSTEM_ANNOUNCEMENT = "system_announcement"

    # Account notifications
    WELCOME = "welcome"
    PASSWORD_CHANGED = "password_changed"


class NotificationCategory(str, Enum):
    """Enumeration of notification categories."""

    BILLING = "billing"
    DOCUMENT = "document"
    SYSTEM = "system"
    ACCOUNT = "account"


class NotificationPriority(str, Enum):
    """Enumeration of notification priorities."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Notification(Base, TimestampMixin):
    """Notification model for user notifications."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # User who receives the notification
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Notification details
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(
        String(10), default=NotificationPriority.LOW.value, nullable=False
    )

    # Read status
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Optional action URL
    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Additional data
    extra_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Auto-delete after expiry
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_notifications_user_unread", "user_id", "read_at"),
        Index("ix_notifications_user_created", "user_id", "created_at"),
        Index("ix_notifications_expires", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type})>"
