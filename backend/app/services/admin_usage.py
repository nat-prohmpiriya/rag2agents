"""Admin usage analytics service.

Fetches usage data from LiteLLM and aggregates for admin dashboard.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import httpx

from app.config import settings
from app.core.telemetry import traced

logger = logging.getLogger(__name__)


@traced()
async def get_spend_logs(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    user_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    Get detailed spend logs from LiteLLM.

    Args:
        start_date: Start of date range
        end_date: End of date range
        user_id: Filter by specific user
        limit: Maximum number of logs to return

    Returns:
        List of spend log entries
    """
    if not settings.litellm_api_key:
        logger.warning("LiteLLM API key not configured")
        return []

    url = f"{settings.litellm_api_url}/spend/logs"

    params: dict[str, Any] = {"limit": limit}
    if start_date:
        params["start_date"] = start_date.isoformat()
    if end_date:
        params["end_date"] = end_date.isoformat()
    if user_id:
        params["user_id"] = user_id

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {settings.litellm_api_key}"},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"LiteLLM API error: {e.response.status_code} - {e.response.text}")
        return []
    except httpx.RequestError as e:
        logger.error(f"LiteLLM connection error: {e}")
        return []


@traced()
async def get_spend_by_users(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[dict[str, Any]]:
    """
    Get spend aggregated by user from LiteLLM.

    Returns:
        List of user spend data
    """
    if not settings.litellm_api_key:
        logger.warning("LiteLLM API key not configured")
        return []

    url = f"{settings.litellm_api_url}/spend/users"

    params: dict[str, Any] = {}
    if start_date:
        params["start_date"] = start_date.isoformat()
    if end_date:
        params["end_date"] = end_date.isoformat()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {settings.litellm_api_key}"},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"LiteLLM API error: {e.response.status_code} - {e.response.text}")
        return []
    except httpx.RequestError as e:
        logger.error(f"LiteLLM connection error: {e}")
        return []


@traced()
async def get_global_spend(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict[str, Any]:
    """
    Get global spend summary from LiteLLM.

    Returns:
        Global spend data
    """
    if not settings.litellm_api_key:
        logger.warning("LiteLLM API key not configured")
        return {"spend": 0, "max_budget": None}

    url = f"{settings.litellm_api_url}/global/spend"

    params: dict[str, Any] = {}
    if start_date:
        params["start_date"] = start_date.isoformat()
    if end_date:
        params["end_date"] = end_date.isoformat()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {settings.litellm_api_key}"},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"LiteLLM API error: {e.response.status_code} - {e.response.text}")
        return {"spend": 0, "max_budget": None}
    except httpx.RequestError as e:
        logger.error(f"LiteLLM connection error: {e}")
        return {"spend": 0, "max_budget": None}


@traced()
async def aggregate_usage_by_model(
    logs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Aggregate usage logs by model.

    Args:
        logs: List of spend logs from LiteLLM

    Returns:
        List of model usage aggregations
    """
    model_data: dict[str, dict[str, Any]] = {}

    for log in logs:
        model = log.get("model", "unknown")
        if model not in model_data:
            model_data[model] = {
                "model": model,
                "requests": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "cost": 0.0,
            }

        model_data[model]["requests"] += 1
        model_data[model]["prompt_tokens"] += log.get("prompt_tokens", 0) or 0
        model_data[model]["completion_tokens"] += log.get("completion_tokens", 0) or 0
        model_data[model]["total_tokens"] += log.get("total_tokens", 0) or 0
        model_data[model]["cost"] += log.get("spend", 0) or 0

    return sorted(model_data.values(), key=lambda x: x["cost"], reverse=True)


@traced()
async def aggregate_usage_by_date(
    logs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Aggregate usage logs by date.

    Args:
        logs: List of spend logs from LiteLLM

    Returns:
        List of daily usage data
    """
    date_data: dict[str, dict[str, Any]] = {}

    for log in logs:
        # Parse the timestamp
        timestamp = log.get("startTime") or log.get("created_at")
        if timestamp:
            if isinstance(timestamp, str):
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except ValueError:
                    continue
            else:
                dt = timestamp
            date_str = dt.strftime("%Y-%m-%d")
        else:
            continue

        if date_str not in date_data:
            date_data[date_str] = {
                "date": date_str,
                "requests": 0,
                "tokens": 0,
                "cost": 0.0,
            }

        date_data[date_str]["requests"] += 1
        date_data[date_str]["tokens"] += log.get("total_tokens", 0) or 0
        date_data[date_str]["cost"] += log.get("spend", 0) or 0

    # Sort by date
    return sorted(date_data.values(), key=lambda x: x["date"])


@traced()
async def get_usage_analytics(
    days: int = 30,
) -> dict[str, Any]:
    """
    Get comprehensive usage analytics for admin dashboard.

    Args:
        days: Number of days to look back

    Returns:
        Complete usage analytics data
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Fetch data from LiteLLM
    logs = await get_spend_logs(start_date=start_date, end_date=end_date, limit=10000)
    users_spend = await get_spend_by_users(start_date=start_date, end_date=end_date)
    global_spend = await get_global_spend(start_date=start_date, end_date=end_date)

    # Aggregate data
    by_model = await aggregate_usage_by_model(logs)
    by_date = await aggregate_usage_by_date(logs)

    # Calculate totals
    total_requests = sum(log.get("requests", 1) for log in logs) if logs else 0
    total_tokens = sum(log.get("total_tokens", 0) or 0 for log in logs)
    total_cost = global_spend.get("spend", 0) or sum(log.get("spend", 0) or 0 for log in logs)

    # Today's stats
    today = datetime.utcnow().strftime("%Y-%m-%d")
    today_data = next((d for d in by_date if d["date"] == today), None)

    return {
        "summary": {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "requests_today": today_data["requests"] if today_data else 0,
            "tokens_today": today_data["tokens"] if today_data else 0,
            "cost_today": today_data["cost"] if today_data else 0,
            "period_days": days,
        },
        "by_user": users_spend[:50] if users_spend else [],  # Top 50 users
        "by_model": by_model,
        "by_date": by_date,
    }


@traced()
async def get_usage_by_plan(
    days: int = 30,
) -> list[dict[str, Any]]:
    """
    Get usage aggregated by plan.

    This requires mapping users to their plans which needs DB access.
    For now, returns placeholder data.

    Args:
        days: Number of days to look back

    Returns:
        List of plan usage data
    """
    # TODO: Implement when we have user->plan mapping in LiteLLM metadata
    return []
