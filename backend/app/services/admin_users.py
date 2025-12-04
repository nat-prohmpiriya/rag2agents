"""Admin user management service."""

import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.telemetry import traced
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.message import Message
from app.models.plan import Plan
from app.models.subscription import BillingInterval, Subscription, SubscriptionStatus
from app.models.user import User
from app.schemas.admin import AdminUserUpdate


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


@traced()
async def get_user_detail(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> dict[str, Any] | None:
    """Get complete user details for admin user detail page."""
    # Get user with all relationships
    query = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.subscriptions).selectinload(Subscription.plan),
            selectinload(User.invoices),
            selectinload(User.projects),
        )
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        return None

    # Get conversation count and recent conversations
    conv_count_query = select(func.count()).where(Conversation.user_id == user_id)
    conv_count_result = await db.execute(conv_count_query)
    total_conversations = conv_count_result.scalar() or 0

    # Get recent conversations with message count
    recent_conv_query = (
        select(
            Conversation.id,
            Conversation.title,
            Conversation.created_at,
            func.count(Message.id).label("message_count"),
            func.max(Message.created_at).label("last_message_at"),
        )
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .where(Conversation.user_id == user_id)
        .group_by(Conversation.id)
        .order_by(Conversation.created_at.desc())
        .limit(10)
    )
    recent_conv_result = await db.execute(recent_conv_query)
    recent_conversations = [
        {
            "id": row.id,
            "title": row.title,
            "message_count": row.message_count,
            "last_message_at": row.last_message_at,
            "created_at": row.created_at,
        }
        for row in recent_conv_result.all()
    ]

    # Get document count and recent documents
    doc_count_query = select(func.count()).where(Document.user_id == user_id)
    doc_count_result = await db.execute(doc_count_query)
    total_documents = doc_count_result.scalar() or 0

    recent_doc_query = (
        select(Document)
        .where(Document.user_id == user_id)
        .order_by(Document.created_at.desc())
        .limit(10)
    )
    recent_doc_result = await db.execute(recent_doc_query)
    recent_documents = [
        {
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "status": doc.status.value if hasattr(doc.status, "value") else doc.status,
            "chunk_count": doc.chunk_count,
            "created_at": doc.created_at,
        }
        for doc in recent_doc_result.scalars().all()
    ]

    # Get project count
    total_projects = len(user.projects)

    # Process subscriptions
    active_subscription = None
    subscription_history = []

    for sub in user.subscriptions:
        price = 0.0
        if sub.plan:
            price = (
                float(sub.plan.price_yearly or 0)
                if sub.billing_interval == BillingInterval.YEARLY
                else float(sub.plan.price_monthly or 0)
            )

        sub_detail = {
            "id": sub.id,
            "plan_name": sub.plan.name if sub.plan else "Unknown",
            "plan_display_name": sub.plan.display_name if sub.plan else "Unknown",
            "status": sub.status.value if hasattr(sub.status, "value") else sub.status,
            "billing_interval": sub.billing_interval.value if hasattr(sub.billing_interval, "value") else sub.billing_interval,
            "price": price,
            "start_date": sub.start_date,
            "current_period_start": sub.current_period_start,
            "current_period_end": sub.current_period_end,
            "trial_end_date": sub.trial_end_date,
            "canceled_at": sub.canceled_at,
            "cancel_reason": sub.cancel_reason,
        }

        if sub.status == SubscriptionStatus.ACTIVE:
            active_subscription = sub_detail
        subscription_history.append(sub_detail)

    # Calculate usage stats (placeholder - TODO: integrate with LiteLLM)
    usage = {
        "tokens_used_today": 0,
        "tokens_used_this_month": 0,
        "tokens_limit": active_subscription["price"] * 10000 if active_subscription else 10000,  # placeholder
        "requests_today": 0,
        "requests_this_month": 0,
        "cost_today": 0.0,
        "cost_this_month": 0.0,
    }

    # Generate usage history (placeholder - TODO: integrate with LiteLLM)
    usage_history = []
    for i in range(30):
        date = datetime.utcnow() - timedelta(days=29 - i)
        usage_history.append({
            "date": date.strftime("%Y-%m-%d"),
            "tokens": 0,
            "requests": 0,
            "cost": 0.0,
        })

    # Process invoices
    invoices = [
        {
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "status": inv.status.value if hasattr(inv.status, "value") else inv.status,
            "total": float(inv.total),
            "amount_paid": float(inv.amount_paid),
            "currency": inv.currency,
            "invoice_date": inv.invoice_date,
            "paid_at": inv.paid_at,
        }
        for inv in sorted(user.invoices, key=lambda x: x.invoice_date, reverse=True)[:10]
    ]

    # Calculate total revenue
    total_revenue = 0.0
    for inv in user.invoices:
        status_value = inv.status.value if hasattr(inv.status, "value") else inv.status
        if status_value == "paid":
            total_revenue += float(inv.amount_paid or 0)

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "tier": user.tier,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "active_subscription": active_subscription,
        "subscription_history": subscription_history,
        "usage": usage,
        "usage_history": usage_history,
        "total_conversations": total_conversations,
        "total_documents": total_documents,
        "total_projects": total_projects,
        "total_revenue": total_revenue,
        "invoices": invoices,
        "recent_conversations": recent_conversations,
        "recent_documents": recent_documents,
    }
