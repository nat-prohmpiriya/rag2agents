"""Admin statistics service."""

import logging
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.telemetry import traced
from app.models.invoice import Invoice, InvoiceStatus
from app.models.plan import Plan
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User
from app.schemas.admin import (
    DailyUsage,
    DashboardStats,
    PlanSubscriberCount,
    RevenueStats,
    UsageStats,
    UserStats,
)

logger = logging.getLogger(__name__)


@traced()
async def get_user_stats(db: AsyncSession) -> UserStats:
    """Get user statistics."""
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # Total users
    total_stmt = select(func.count(User.id))
    total_users = (await db.execute(total_stmt)).scalar() or 0

    # Active today (users who logged in today - approximated by updated_at)
    active_stmt = select(func.count(User.id)).where(User.updated_at >= today_start)
    active_today = (await db.execute(active_stmt)).scalar() or 0

    # New this week
    new_week_stmt = select(func.count(User.id)).where(User.created_at >= week_ago)
    new_this_week = (await db.execute(new_week_stmt)).scalar() or 0

    # New this month
    new_month_stmt = select(func.count(User.id)).where(User.created_at >= month_ago)
    new_this_month = (await db.execute(new_month_stmt)).scalar() or 0

    return UserStats(
        total_users=total_users,
        active_today=active_today,
        new_this_week=new_this_week,
        new_this_month=new_this_month,
    )


@traced()
async def get_usage_stats_from_litellm() -> UsageStats:
    """Get usage statistics from LiteLLM."""
    if not settings.litellm_api_key:
        return UsageStats(
            requests_today=0,
            requests_this_month=0,
            tokens_today=0,
            tokens_this_month=0,
            cost_today=0.0,
            cost_this_month=0.0,
        )

    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    try:
        async with httpx.AsyncClient() as client:
            # Get spend data from LiteLLM
            response = await client.get(
                f"{settings.litellm_api_url}/spend/logs",
                headers={"Authorization": f"Bearer {settings.litellm_api_key}"},
                params={
                    "start_date": month_start.isoformat(),
                    "end_date": now.isoformat(),
                },
                timeout=30.0,
            )

            if response.status_code != 200:
                logger.warning(f"LiteLLM spend API returned {response.status_code}")
                return UsageStats(
                    requests_today=0,
                    requests_this_month=0,
                    tokens_today=0,
                    tokens_this_month=0,
                    cost_today=0.0,
                    cost_this_month=0.0,
                )

            data = response.json()
            spend_logs = data if isinstance(data, list) else data.get("data", [])

            requests_today = 0
            requests_this_month = 0
            tokens_today = 0
            tokens_this_month = 0
            cost_today = 0.0
            cost_this_month = 0.0

            for log in spend_logs:
                log_time = datetime.fromisoformat(
                    log.get("startTime", log.get("created_at", now.isoformat())).replace("Z", "+00:00")
                )
                tokens = log.get("total_tokens", 0)
                cost = log.get("spend", 0.0)

                requests_this_month += 1
                tokens_this_month += tokens
                cost_this_month += cost

                if log_time >= today_start:
                    requests_today += 1
                    tokens_today += tokens
                    cost_today += cost

            return UsageStats(
                requests_today=requests_today,
                requests_this_month=requests_this_month,
                tokens_today=tokens_today,
                tokens_this_month=tokens_this_month,
                cost_today=round(cost_today, 4),
                cost_this_month=round(cost_this_month, 4),
            )

    except Exception as e:
        logger.error(f"Error fetching LiteLLM stats: {e}")
        return UsageStats(
            requests_today=0,
            requests_this_month=0,
            tokens_today=0,
            tokens_this_month=0,
            cost_today=0.0,
            cost_this_month=0.0,
        )


@traced()
async def get_revenue_stats(db: AsyncSession) -> RevenueStats:
    """Get revenue statistics."""
    now = datetime.now(UTC)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Calculate MRR from active subscriptions
    mrr_stmt = (
        select(func.sum(Plan.price_monthly))
        .select_from(Subscription)
        .join(Plan)
        .where(
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING])
        )
    )
    mrr = (await db.execute(mrr_stmt)).scalar() or 0.0

    # ARR is MRR * 12
    arr = float(mrr) * 12

    # Total revenue from paid invoices
    total_stmt = select(func.sum(Invoice.amount_paid)).where(
        Invoice.status == InvoiceStatus.PAID
    )
    total_revenue = (await db.execute(total_stmt)).scalar() or 0.0

    # Revenue this month
    month_stmt = select(func.sum(Invoice.amount_paid)).where(
        Invoice.status == InvoiceStatus.PAID,
        Invoice.paid_at >= month_start,
    )
    revenue_this_month = (await db.execute(month_stmt)).scalar() or 0.0

    return RevenueStats(
        mrr=round(float(mrr), 2),
        arr=round(arr, 2),
        total_revenue=round(float(total_revenue), 2),
        revenue_this_month=round(float(revenue_this_month), 2),
    )


@traced()
async def get_subscribers_by_plan(db: AsyncSession) -> list[PlanSubscriberCount]:
    """Get subscriber count per plan."""
    # Get all plans with subscriber counts
    stmt = (
        select(
            Plan.id,
            Plan.name,
            Plan.display_name,
            func.count(Subscription.id).label("subscriber_count"),
        )
        .outerjoin(
            Subscription,
            (Subscription.plan_id == Plan.id)
            & Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]),
        )
        .where(Plan.is_active.is_(True))
        .group_by(Plan.id, Plan.name, Plan.display_name)
        .order_by(Plan.price_monthly)
    )

    result = await db.execute(stmt)
    rows = result.all()

    total_subscribers = sum(row.subscriber_count for row in rows)

    return [
        PlanSubscriberCount(
            plan_id=str(row.id),
            plan_name=row.name,
            display_name=row.display_name,
            subscriber_count=row.subscriber_count,
            percentage=round(
                (row.subscriber_count / total_subscribers * 100) if total_subscribers > 0 else 0, 1
            ),
        )
        for row in rows
    ]


@traced()
async def get_usage_over_time() -> list[DailyUsage]:
    """Get daily usage data for the last 30 days."""
    if not settings.litellm_api_key:
        return []

    now = datetime.now(UTC)
    start_date = now - timedelta(days=30)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.litellm_api_url}/spend/logs",
                headers={"Authorization": f"Bearer {settings.litellm_api_key}"},
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": now.isoformat(),
                },
                timeout=30.0,
            )

            if response.status_code != 200:
                return []

            data = response.json()
            spend_logs = data if isinstance(data, list) else data.get("data", [])

            # Aggregate by date
            daily_data: dict[str, DailyUsage] = {}

            for log in spend_logs:
                log_time = datetime.fromisoformat(
                    log.get("startTime", log.get("created_at", now.isoformat())).replace("Z", "+00:00")
                )
                date_str = log_time.strftime("%Y-%m-%d")

                if date_str not in daily_data:
                    daily_data[date_str] = DailyUsage(
                        date=date_str, requests=0, tokens=0, cost=0.0
                    )

                daily_data[date_str].requests += 1
                daily_data[date_str].tokens += log.get("total_tokens", 0)
                daily_data[date_str].cost += log.get("spend", 0.0)

            # Fill in missing dates
            result = []
            current = start_date
            while current <= now:
                date_str = current.strftime("%Y-%m-%d")
                if date_str in daily_data:
                    usage = daily_data[date_str]
                    result.append(
                        DailyUsage(
                            date=date_str,
                            requests=usage.requests,
                            tokens=usage.tokens,
                            cost=round(usage.cost, 4),
                        )
                    )
                else:
                    result.append(DailyUsage(date=date_str, requests=0, tokens=0, cost=0.0))
                current += timedelta(days=1)

            return result

    except Exception as e:
        logger.error(f"Error fetching LiteLLM usage over time: {e}")
        return []


@traced()
async def get_dashboard_stats(db: AsyncSession) -> DashboardStats:
    """Get all dashboard statistics."""
    user_stats = await get_user_stats(db)
    usage_stats = await get_usage_stats_from_litellm()
    revenue_stats = await get_revenue_stats(db)
    subscribers_by_plan = await get_subscribers_by_plan(db)
    usage_over_time = await get_usage_over_time()

    return DashboardStats(
        users=user_stats,
        usage=usage_stats,
        revenue=revenue_stats,
        subscribers_by_plan=subscribers_by_plan,
        usage_over_time=usage_over_time,
    )
