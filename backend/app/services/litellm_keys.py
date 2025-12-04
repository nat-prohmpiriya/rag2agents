"""LiteLLM Key Management Service.

This service manages virtual keys in LiteLLM for subscription-based access control.
Provides functions for creating, updating, and managing API keys with plan-based limits.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

import httpx

from app.config import settings
from app.core.telemetry import traced
from app.models.plan import Plan

logger = logging.getLogger(__name__)


def calculate_tpm_limit(plan: Plan) -> int:
    """
    Calculate tokens per minute limit from monthly token quota.

    Formula: monthly_tokens / 30 days / 24 hours / 60 minutes
    With a minimum of 100 TPM.

    Args:
        plan: The subscription plan

    Returns:
        Tokens per minute limit
    """
    monthly_tokens = plan.tokens_per_month
    # Calculate average TPM from monthly quota
    tpm = monthly_tokens // (30 * 24 * 60)
    # Ensure minimum TPM and add some buffer (2x) for burst usage
    return max(100, tpm * 2)


def calculate_max_budget(plan: Plan, billing_interval: str = "monthly") -> float | None:
    """
    Calculate max budget for the key based on plan pricing.

    For cost tracking, we set max_budget to the plan's API cost allowance.
    This is typically a percentage of the plan price (e.g., 80% goes to API costs).

    Args:
        plan: The subscription plan
        billing_interval: "monthly" or "yearly"

    Returns:
        Max budget in USD, or None for unlimited
    """
    if plan.plan_type.value == "enterprise":
        # Enterprise plans typically have custom/unlimited budgets
        return None

    # Calculate API cost allowance (assume 70% of plan price goes to API costs)
    api_cost_ratio = 0.7

    if billing_interval == "yearly" and plan.price_yearly:
        monthly_price = float(plan.price_yearly) / 12
    else:
        monthly_price = float(plan.price_monthly)

    if monthly_price <= 0:
        # Free plan - set a small budget for protection
        return 1.0

    return round(monthly_price * api_cost_ratio, 2)


class LiteLLMKeyError(Exception):
    """Exception for LiteLLM key management errors."""

    pass


@traced()
async def create_virtual_key(
    user_id: uuid.UUID,
    plan: Plan,
    user_email: str,
    team_id: str | None = None,
    billing_interval: str = "monthly",
) -> dict[str, Any]:
    """
    Create a virtual key in LiteLLM for a user subscription.

    The key is configured with:
    - max_budget: Based on plan price (70% allocated to API costs)
    - tpm_limit: Calculated from monthly token quota
    - rpm_limit: From plan.requests_per_minute
    - models: From plan.allowed_models

    Args:
        user_id: The user's ID
        plan: The subscription plan
        user_email: User's email for identification
        team_id: Optional team ID
        billing_interval: "monthly" or "yearly"

    Returns:
        Dict containing key_id, api_key, and configuration
    """
    if not settings.litellm_api_key:
        logger.warning("LiteLLM API key not configured, skipping key creation")
        return {"key_id": None, "api_key": None}

    url = f"{settings.litellm_api_url}/key/generate"

    # Calculate limits from plan
    tpm_limit = calculate_tpm_limit(plan)
    max_budget = calculate_max_budget(plan, billing_interval)

    payload: dict[str, Any] = {
        "user_id": str(user_id),
        "key_alias": f"sub_{user_id}",
        "metadata": {
            "user_email": user_email,
            "plan_id": str(plan.id),
            "plan_name": plan.name,
            "plan_type": plan.plan_type.value,
            "billing_interval": billing_interval,
            "tokens_per_month": plan.tokens_per_month,
            "created_at": datetime.utcnow().isoformat(),
        },
        "models": plan.allowed_models if plan.allowed_models else [],
        "tpm_limit": tpm_limit,
        "rpm_limit": plan.requests_per_minute,
        "max_parallel_requests": max(1, plan.requests_per_minute // 2),
    }

    # Only set max_budget if not None (unlimited for enterprise)
    if max_budget is not None:
        payload["max_budget"] = max_budget

    if team_id:
        payload["team_id"] = team_id

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.litellm_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            logger.info(
                f"Created LiteLLM key for user {user_id}: "
                f"tpm={tpm_limit}, rpm={plan.requests_per_minute}, budget={max_budget}"
            )

            return {
                "key_id": data.get("key"),
                "api_key": data.get("key"),
                "token": data.get("token"),
                "tpm_limit": tpm_limit,
                "rpm_limit": plan.requests_per_minute,
                "max_budget": max_budget,
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"LiteLLM API error: {e.response.status_code} - {e.response.text}")
        raise LiteLLMKeyError(f"Failed to create key: {e.response.text}") from e
    except httpx.RequestError as e:
        logger.error(f"LiteLLM connection error: {e}")
        raise LiteLLMKeyError(f"Failed to connect to LiteLLM: {e}") from e


@traced()
async def update_virtual_key(
    key_id: str,
    plan: Plan,
    billing_interval: str = "monthly",
) -> bool:
    """
    Update a virtual key in LiteLLM with new plan limits.

    Args:
        key_id: The LiteLLM key ID
        plan: The new plan with updated limits
        billing_interval: "monthly" or "yearly"

    Returns:
        True if successful
    """
    if not settings.litellm_api_key or not key_id:
        logger.warning("LiteLLM not configured or no key_id, skipping key update")
        return False

    url = f"{settings.litellm_api_url}/key/update"

    # Calculate new limits from plan
    tpm_limit = calculate_tpm_limit(plan)
    max_budget = calculate_max_budget(plan, billing_interval)

    payload: dict[str, Any] = {
        "key": key_id,
        "models": plan.allowed_models if plan.allowed_models else [],
        "tpm_limit": tpm_limit,
        "rpm_limit": plan.requests_per_minute,
        "max_parallel_requests": max(1, plan.requests_per_minute // 2),
        "metadata": {
            "plan_id": str(plan.id),
            "plan_name": plan.name,
            "plan_type": plan.plan_type.value,
            "billing_interval": billing_interval,
            "tokens_per_month": plan.tokens_per_month,
            "updated_at": datetime.utcnow().isoformat(),
        },
    }

    if max_budget is not None:
        payload["max_budget"] = max_budget

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.litellm_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
            response.raise_for_status()

            logger.info(
                f"Updated LiteLLM key {key_id}: "
                f"tpm={tpm_limit}, rpm={plan.requests_per_minute}, budget={max_budget}"
            )
            return True

    except httpx.HTTPStatusError as e:
        logger.error(f"LiteLLM API error: {e.response.status_code} - {e.response.text}")
        raise LiteLLMKeyError(f"Failed to update key: {e.response.text}") from e
    except httpx.RequestError as e:
        logger.error(f"LiteLLM connection error: {e}")
        raise LiteLLMKeyError(f"Failed to connect to LiteLLM: {e}") from e


@traced()
async def delete_virtual_key(key_id: str) -> bool:
    """
    Delete a virtual key in LiteLLM.

    Args:
        key_id: The LiteLLM key ID

    Returns:
        True if successful
    """
    if not settings.litellm_api_key or not key_id:
        logger.warning("LiteLLM not configured or no key_id, skipping key deletion")
        return False

    url = f"{settings.litellm_api_url}/key/delete"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={"keys": [key_id]},
                headers={
                    "Authorization": f"Bearer {settings.litellm_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
            response.raise_for_status()

            logger.info(f"Deleted LiteLLM key {key_id}")
            return True

    except httpx.HTTPStatusError as e:
        logger.error(f"LiteLLM API error: {e.response.status_code} - {e.response.text}")
        raise LiteLLMKeyError(f"Failed to delete key: {e.response.text}") from e
    except httpx.RequestError as e:
        logger.error(f"LiteLLM connection error: {e}")
        raise LiteLLMKeyError(f"Failed to connect to LiteLLM: {e}") from e


@traced()
async def get_key_info(key_id: str) -> dict[str, Any] | None:
    """
    Get information about a virtual key.

    Args:
        key_id: The LiteLLM key ID

    Returns:
        Key information or None if not found
    """
    if not settings.litellm_api_key or not key_id:
        return None

    url = f"{settings.litellm_api_url}/key/info"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params={"key": key_id},
                headers={
                    "Authorization": f"Bearer {settings.litellm_api_key}",
                },
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        logger.error(f"LiteLLM API error: {e.response.status_code}")
        return None
    except httpx.RequestError as e:
        logger.error(f"LiteLLM connection error: {e}")
        return None


@traced()
async def disable_virtual_key(key_id: str) -> bool:
    """
    Disable a virtual key (for canceled subscriptions).

    Args:
        key_id: The LiteLLM key ID

    Returns:
        True if successful
    """
    if not settings.litellm_api_key or not key_id:
        return False

    url = f"{settings.litellm_api_url}/key/update"

    payload = {
        "key": key_id,
        "models": [],  # Remove all model access
        "rpm_limit": 0,
        "max_parallel_requests": 0,
        "metadata": {
            "disabled": True,
            "disabled_at": datetime.utcnow().isoformat(),
        },
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.litellm_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
            response.raise_for_status()

            logger.info(f"Disabled LiteLLM key {key_id}")
            return True

    except httpx.HTTPStatusError as e:
        logger.error(f"LiteLLM API error: {e.response.status_code}")
        return False
    except httpx.RequestError as e:
        logger.error(f"LiteLLM connection error: {e}")
        return False


@traced()
async def get_user_usage(
    user_id: uuid.UUID,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict[str, Any]:
    """
    Get usage statistics for a specific user from LiteLLM.

    Args:
        user_id: The user's ID
        start_date: Start of date range (defaults to 30 days ago)
        end_date: End of date range (defaults to now)

    Returns:
        Dict containing usage statistics
    """
    if not settings.litellm_api_key:
        logger.warning("LiteLLM API key not configured")
        return {
            "total_tokens": 0,
            "total_requests": 0,
            "total_cost": 0.0,
            "tokens_today": 0,
            "requests_today": 0,
            "cost_today": 0.0,
        }

    # Default date range: last 30 days
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    url = f"{settings.litellm_api_url}/spend/logs"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params={
                    "user_id": str(user_id),
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                headers={
                    "Authorization": f"Bearer {settings.litellm_api_key}",
                },
                timeout=30.0,
            )
            response.raise_for_status()
            logs = response.json()

            # Aggregate usage from logs
            total_tokens = 0
            total_requests = 0
            total_cost = 0.0
            tokens_today = 0
            requests_today = 0
            cost_today = 0.0

            today = datetime.utcnow().strftime("%Y-%m-%d")

            for log in logs:
                tokens = log.get("total_tokens", 0) or 0
                cost = log.get("spend", 0) or 0

                total_tokens += tokens
                total_requests += 1
                total_cost += cost

                # Check if this log is from today
                log_time = log.get("startTime") or log.get("created_at")
                if log_time and isinstance(log_time, str) and log_time.startswith(today):
                    tokens_today += tokens
                    requests_today += 1
                    cost_today += cost

            return {
                "total_tokens": total_tokens,
                "total_requests": total_requests,
                "total_cost": round(total_cost, 4),
                "tokens_today": tokens_today,
                "requests_today": requests_today,
                "cost_today": round(cost_today, 4),
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"LiteLLM API error: {e.response.status_code}")
        return {
            "total_tokens": 0,
            "total_requests": 0,
            "total_cost": 0.0,
            "tokens_today": 0,
            "requests_today": 0,
            "cost_today": 0.0,
            "error": f"API error: {e.response.status_code}",
        }
    except httpx.RequestError as e:
        logger.error(f"LiteLLM connection error: {e}")
        return {
            "total_tokens": 0,
            "total_requests": 0,
            "total_cost": 0.0,
            "tokens_today": 0,
            "requests_today": 0,
            "cost_today": 0.0,
            "error": f"Connection error: {e}",
        }


@traced()
async def reset_key_budget(key_id: str) -> bool:
    """
    Reset the budget for a key (e.g., at the start of a new billing period).

    Args:
        key_id: The LiteLLM key ID

    Returns:
        True if successful
    """
    if not settings.litellm_api_key or not key_id:
        return False

    url = f"{settings.litellm_api_url}/key/update"

    payload = {
        "key": key_id,
        "spend": 0,  # Reset spend to 0
        "metadata": {
            "budget_reset_at": datetime.utcnow().isoformat(),
        },
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.litellm_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
            response.raise_for_status()

            logger.info(f"Reset budget for LiteLLM key {key_id}")
            return True

    except httpx.HTTPStatusError as e:
        logger.error(f"LiteLLM API error: {e.response.status_code}")
        return False
    except httpx.RequestError as e:
        logger.error(f"LiteLLM connection error: {e}")
        return False


@traced()
async def enable_virtual_key(key_id: str, plan: Plan) -> bool:
    """
    Re-enable a disabled virtual key with plan limits.

    Args:
        key_id: The LiteLLM key ID
        plan: The plan to restore limits from

    Returns:
        True if successful
    """
    if not settings.litellm_api_key or not key_id:
        return False

    tpm_limit = calculate_tpm_limit(plan)

    url = f"{settings.litellm_api_url}/key/update"

    payload = {
        "key": key_id,
        "models": plan.allowed_models if plan.allowed_models else [],
        "tpm_limit": tpm_limit,
        "rpm_limit": plan.requests_per_minute,
        "max_parallel_requests": max(1, plan.requests_per_minute // 2),
        "metadata": {
            "disabled": False,
            "enabled_at": datetime.utcnow().isoformat(),
        },
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.litellm_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
            response.raise_for_status()

            logger.info(f"Enabled LiteLLM key {key_id}")
            return True

    except httpx.HTTPStatusError as e:
        logger.error(f"LiteLLM API error: {e.response.status_code}")
        return False
    except httpx.RequestError as e:
        logger.error(f"LiteLLM connection error: {e}")
        return False


# Convenience functions for subscription flow


async def create_key_for_subscription(
    user_id: uuid.UUID,
    user_email: str,
    plan: Plan,
    billing_interval: str = "monthly",
) -> dict[str, Any]:
    """
    Convenience function to create a key for a new subscription.

    Args:
        user_id: The user's ID
        user_email: User's email
        plan: The subscription plan
        billing_interval: "monthly" or "yearly"

    Returns:
        Dict containing key_id and api_key
    """
    return await create_virtual_key(
        user_id=user_id,
        plan=plan,
        user_email=user_email,
        billing_interval=billing_interval,
    )


async def update_key_for_plan_change(
    key_id: str,
    new_plan: Plan,
    billing_interval: str = "monthly",
) -> bool:
    """
    Update a key when the user changes their plan.

    Args:
        key_id: The LiteLLM key ID
        new_plan: The new subscription plan
        billing_interval: "monthly" or "yearly"

    Returns:
        True if successful
    """
    return await update_virtual_key(
        key_id=key_id,
        plan=new_plan,
        billing_interval=billing_interval,
    )


async def suspend_key_for_subscription(key_id: str) -> bool:
    """
    Disable a key when subscription is canceled or suspended.

    Args:
        key_id: The LiteLLM key ID

    Returns:
        True if successful
    """
    return await disable_virtual_key(key_id)


async def reactivate_key_for_subscription(key_id: str, plan: Plan) -> bool:
    """
    Re-enable a key when subscription is reactivated.

    Args:
        key_id: The LiteLLM key ID
        plan: The subscription plan

    Returns:
        True if successful
    """
    return await enable_virtual_key(key_id, plan)
