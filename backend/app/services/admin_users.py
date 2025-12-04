"""Admin user management service."""

import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.tracing import traced
from app.models.invoice import Invoice
from app.models.plan import Plan
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User
from app.schemas.admin import AdminUserResponse, AdminUserUpdate


@traced()
async def get_users_with_details(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    search: str | None = None,
    plan_filter: str | None = None,
    status_filter: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Get users with subscription and usage details for admin panel."""
    # Base query with eager loading
    query = (
        select(User)
        .options(
            selectinload(User.subscriptions).selectinload(Subscription.plan),
            selectinload(User.invoices),
        )
        .order_by(User.created_at.desc())
    )

    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                User.email.ilike(search_term),
                User.username.ilike(search_term),
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
            )
        )

    # Apply plan filter
    if plan_filter and plan_filter != "all":
        query = query.where(User.tier == plan_filter)

    # Apply status filter
    if status_filter and status_filter != "all":
        if status_filter == "active":
            query = query.where(User.is_active.is_(True))
        elif status_filter == "inactive":
            query = query.where(User.is_active.is_(False))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    users = result.scalars().all()

    # Process users and calculate additional data
    user_data = []
    for user in users:
        # Get active subscription
        active_sub = next(
            (s for s in user.subscriptions if s.status == SubscriptionStatus.ACTIVE),
            None,
        )

        # Calculate total revenue from invoices
        revenue_total = sum(
            inv.amount_paid or 0
            for inv in user.invoices
            if inv.status == "paid"
        )

        # Determine user status
        status = "active" if user.is_active else "inactive"

        # Get plan info
        plan_name = None
        subscription_status = None
        tokens_limit = 0

        if active_sub and active_sub.plan:
            plan_name = active_sub.plan.display_name
            subscription_status = active_sub.status.value
            tokens_limit = active_sub.plan.tokens_per_month

        user_data.append({
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "tier": user.tier,
            "status": status,
            "plan_name": plan_name,
            "subscription_status": subscription_status,
            "tokens_used": 0,  # TODO: Get from LiteLLM
            "tokens_limit": tokens_limit,
            "revenue_total": float(revenue_total),
            "last_active": user.updated_at,  # Use updated_at as proxy for last_active
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        })

    return user_data, total


@traced()
async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Get a user by ID with subscriptions."""
    query = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.subscriptions).selectinload(Subscription.plan),
            selectinload(User.invoices),
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


@traced()
async def update_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: AdminUserUpdate,
) -> User | None:
    """Update a user's information."""
    user = await get_user_by_id(db, user_id)
    if not user:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    return user


@traced()
async def suspend_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    reason: str | None = None,
) -> User | None:
    """Suspend a user account."""
    user = await get_user_by_id(db, user_id)
    if not user:
        return None

    user.is_active = False

    # Cancel active subscriptions
    for sub in user.subscriptions:
        if sub.status == SubscriptionStatus.ACTIVE:
            sub.status = SubscriptionStatus.CANCELED
            sub.canceled_at = datetime.utcnow()
            sub.cancel_reason = reason or "Account suspended by admin"

    return user


@traced()
async def activate_user(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> User | None:
    """Activate a suspended user account."""
    user = await get_user_by_id(db, user_id)
    if not user:
        return None

    user.is_active = True
    return user


@traced()
async def ban_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    reason: str | None = None,
) -> User | None:
    """Ban a user (suspend + mark as banned)."""
    user = await suspend_user(db, user_id, reason or "Banned by admin")
    return user


@traced()
async def delete_user(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> bool:
    """Delete a user and all their data."""
    user = await get_user_by_id(db, user_id)
    if not user:
        return False

    await db.delete(user)
    return True


@traced()
async def change_user_plan(
    db: AsyncSession,
    user_id: uuid.UUID,
    plan_id: uuid.UUID,
) -> Subscription | None:
    """Change a user's subscription plan."""
    # Get user
    user = await get_user_by_id(db, user_id)
    if not user:
        return None

    # Get the new plan
    plan_query = select(Plan).where(Plan.id == plan_id)
    plan_result = await db.execute(plan_query)
    plan = plan_result.scalar_one_or_none()
    if not plan:
        return None

    # Cancel existing active subscription
    for sub in user.subscriptions:
        if sub.status == SubscriptionStatus.ACTIVE:
            sub.status = SubscriptionStatus.CANCELED
            sub.canceled_at = datetime.utcnow()
            sub.cancel_reason = "Plan changed by admin"

    # Create new subscription
    new_subscription = Subscription(
        user_id=user_id,
        plan_id=plan_id,
        status=SubscriptionStatus.ACTIVE,
        start_date=datetime.utcnow(),
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30),
    )
    db.add(new_subscription)

    # Update user tier
    user.tier = plan.plan_type

    return new_subscription


@traced()
async def bulk_change_plan(
    db: AsyncSession,
    user_ids: list[uuid.UUID],
    plan_id: uuid.UUID,
) -> list[dict[str, Any]]:
    """Change plan for multiple users."""
    results = []
    for user_id in user_ids:
        try:
            sub = await change_user_plan(db, user_id, plan_id)
            results.append({
                "success": sub is not None,
                "user_id": user_id,
                "message": "Plan changed successfully" if sub else "User or plan not found",
            })
        except Exception as e:
            results.append({
                "success": False,
                "user_id": user_id,
                "message": str(e),
            })
    return results


@traced()
async def bulk_suspend(
    db: AsyncSession,
    user_ids: list[uuid.UUID],
    reason: str | None = None,
) -> list[dict[str, Any]]:
    """Suspend multiple users."""
    results = []
    for user_id in user_ids:
        try:
            user = await suspend_user(db, user_id, reason)
            results.append({
                "success": user is not None,
                "user_id": user_id,
                "message": "User suspended" if user else "User not found",
            })
        except Exception as e:
            results.append({
                "success": False,
                "user_id": user_id,
                "message": str(e),
            })
    return results


@traced()
async def bulk_activate(
    db: AsyncSession,
    user_ids: list[uuid.UUID],
) -> list[dict[str, Any]]:
    """Activate multiple users."""
    results = []
    for user_id in user_ids:
        try:
            user = await activate_user(db, user_id)
            results.append({
                "success": user is not None,
                "user_id": user_id,
                "message": "User activated" if user else "User not found",
            })
        except Exception as e:
            results.append({
                "success": False,
                "user_id": user_id,
                "message": str(e),
            })
    return results


def calculate_pages(total: int, per_page: int) -> int:
    """Calculate total number of pages."""
    if per_page <= 0:
        return 0
    return (total + per_page - 1) // per_page
