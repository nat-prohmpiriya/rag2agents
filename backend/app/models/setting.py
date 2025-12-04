"""Settings model for admin configuration."""

import uuid
from enum import Enum

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class SettingCategory(str, Enum):
    """Setting category enumeration."""

    GENERAL = "general"
    PAYMENT = "payment"
    LITELLM = "litellm"
    NOTIFICATION = "notification"


class Setting(Base, TimestampMixin):
    """Application settings model.

    Stores key-value configuration settings for the application.
    Settings are grouped by category for organization.
    """

    __tablename__ = "settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    category: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False, default=SettingCategory.GENERAL.value
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_editable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("ix_settings_category_key", "category", "key"),
    )

    def __repr__(self) -> str:
        return f"<Setting {self.key}={self.value[:20] if self.value else 'null'}>"
