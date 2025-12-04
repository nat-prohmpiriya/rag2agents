"""Plan model for subscription pricing plans."""

import enum
import uuid

from sqlalchemy import Boolean, Enum, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class PlanType(str, enum.Enum):
    """Plan type enumeration."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Plan(Base, TimestampMixin):
    """Plan model for pricing tiers and limits."""

    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_type: Mapped[PlanType] = mapped_column(
        Enum(PlanType),
        default=PlanType.FREE,
        nullable=False,
    )

    # Pricing
    price_monthly: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.0,
        nullable=False,
    )
    price_yearly: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Usage Limits
    tokens_per_month: Mapped[int] = mapped_column(Integer, default=100000, nullable=False)
    requests_per_minute: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    requests_per_day: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    max_documents: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    max_projects: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    max_agents: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Model Access - list of allowed model names
    allowed_models: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=list,
        nullable=False,
    )

    # Features as JSON for flexibility
    features: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Stripe integration
    stripe_price_id_monthly: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_price_id_yearly: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_product_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Plan(id={self.id}, name={self.name}, type={self.plan_type})>"


# Import at the end to avoid circular imports
from app.models.subscription import Subscription  # noqa: E402, F401
