"""Seed script for creating default plans.

Run with: uv run python -m app.scripts.seed_plans
"""

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal
from app.models.plan import Plan, PlanType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Plan definitions
PLANS = [
    {
        "name": "free",
        "display_name": "Free",
        "description": "Perfect for trying out the platform",
        "plan_type": PlanType.FREE,
        "price_monthly": 0,
        "price_yearly": None,
        "currency": "USD",
        "tokens_per_month": 50000,
        "requests_per_month": 100,
        "credits_per_month": 100,
        "requests_per_minute": 5,
        "requests_per_day": 50,
        "max_documents": 10,
        "max_projects": 2,
        "max_agents": 1,
        "allowed_models": [
            "openai/gpt-3.5-turbo",
        ],
        "features": {
            "api_access": False,
            "priority_support": False,
            "custom_tools": False,
            "sso": False,
            "dedicated_support": False,
            "sla": False,
        },
        "is_active": True,
        "is_public": True,
    },
    {
        "name": "starter",
        "display_name": "Starter",
        "description": "For individuals getting started",
        "plan_type": PlanType.STARTER,
        "price_monthly": 9,
        "price_yearly": 86,
        "currency": "USD",
        "tokens_per_month": 500000,
        "requests_per_month": 1000,
        "credits_per_month": 1500,
        "requests_per_minute": 20,
        "requests_per_day": 500,
        "max_documents": 100,
        "max_projects": 10,
        "max_agents": 3,
        "allowed_models": [
            "openai/gpt-3.5-turbo",
            "openai/gpt-4o-mini",
            "google/gemini-1.5-flash",
        ],
        "features": {
            "api_access": True,
            "priority_support": False,
            "custom_tools": False,
            "sso": False,
            "dedicated_support": False,
            "sla": False,
        },
        "is_active": True,
        "is_public": True,
    },
    {
        "name": "pro",
        "display_name": "Pro",
        "description": "For professionals and power users",
        "plan_type": PlanType.PRO,
        "price_monthly": 29,
        "price_yearly": 278,
        "currency": "USD",
        "tokens_per_month": 2000000,
        "requests_per_month": 5000,
        "credits_per_month": 10000,
        "requests_per_minute": 60,
        "requests_per_day": 2000,
        "max_documents": 500,
        "max_projects": 50,
        "max_agents": 10,
        "allowed_models": [
            "openai/gpt-3.5-turbo",
            "openai/gpt-4o-mini",
            "openai/gpt-4o",
            "openai/gpt-4-turbo",
            "google/gemini-1.5-flash",
            "google/gemini-1.5-pro",
            "anthropic/claude-3-haiku",
            "anthropic/claude-3.5-sonnet",
        ],
        "features": {
            "api_access": True,
            "priority_support": True,
            "custom_tools": True,
            "sso": False,
            "dedicated_support": False,
            "sla": False,
        },
        "is_active": True,
        "is_public": True,
    },
    {
        "name": "business",
        "display_name": "Business",
        "description": "For teams and growing businesses",
        "plan_type": PlanType.BUSINESS,
        "price_monthly": 79,
        "price_yearly": 758,
        "currency": "USD",
        "tokens_per_month": 10000000,
        "requests_per_month": 20000,
        "credits_per_month": 50000,
        "requests_per_minute": 120,
        "requests_per_day": 10000,
        "max_documents": 2000,
        "max_projects": 200,
        "max_agents": 30,
        "allowed_models": [
            "openai/gpt-3.5-turbo",
            "openai/gpt-4o-mini",
            "openai/gpt-4o",
            "openai/gpt-4-turbo",
            "google/gemini-1.5-flash",
            "google/gemini-1.5-pro",
            "anthropic/claude-3-haiku",
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-opus",
        ],
        "features": {
            "api_access": True,
            "priority_support": True,
            "custom_tools": True,
            "sso": True,
            "dedicated_support": False,
            "sla": False,
        },
        "is_active": True,
        "is_public": True,
    },
    {
        "name": "enterprise",
        "display_name": "Enterprise",
        "description": "Custom solutions for large organizations",
        "plan_type": PlanType.ENTERPRISE,
        "price_monthly": 0,  # Custom pricing
        "price_yearly": None,
        "currency": "USD",
        "tokens_per_month": -1,  # Unlimited
        "requests_per_month": -1,  # Unlimited
        "credits_per_month": -1,  # Unlimited
        "requests_per_minute": 500,
        "requests_per_day": -1,  # Unlimited
        "max_documents": -1,  # Unlimited
        "max_projects": -1,  # Unlimited
        "max_agents": -1,  # Unlimited
        "allowed_models": [
            "openai/gpt-3.5-turbo",
            "openai/gpt-4o-mini",
            "openai/gpt-4o",
            "openai/gpt-4-turbo",
            "google/gemini-1.5-flash",
            "google/gemini-1.5-pro",
            "anthropic/claude-3-haiku",
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-opus",
        ],
        "features": {
            "api_access": True,
            "priority_support": True,
            "custom_tools": True,
            "sso": True,
            "dedicated_support": True,
            "sla": True,
        },
        "is_active": True,
        "is_public": True,
    },
]


async def seed_plans(db: AsyncSession) -> None:
    """Seed plans into database."""
    logger.info("Seeding plans...")

    for plan_data in PLANS:
        # Check if plan already exists
        stmt = select(Plan).where(Plan.name == plan_data["name"])
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing plan
            for key, value in plan_data.items():
                setattr(existing, key, value)
            logger.info(f"Updated plan: {plan_data['name']}")
        else:
            # Create new plan
            plan = Plan(**plan_data)
            db.add(plan)
            logger.info(f"Created plan: {plan_data['name']}")

    await db.commit()
    logger.info("Plans seeded successfully!")


async def main():
    """Main entry point."""
    async with SessionLocal() as session:
        await seed_plans(session)


if __name__ == "__main__":
    asyncio.run(main())
