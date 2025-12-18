"""Service for fetching available LLM models from LiteLLM."""

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Provider metadata for enriching model info
PROVIDER_METADATA: dict[str, dict[str, str]] = {
    "gemini": {
        "display_name": "Google",
        "website_url": "https://ai.google.dev",
        "pricing_url": "https://ai.google.dev/pricing",
        "terms_url": "https://policies.google.com/terms",
        "privacy_url": "https://policies.google.com/privacy",
    },
    "openai": {
        "display_name": "OpenAI",
        "website_url": "https://openai.com",
        "pricing_url": "https://openai.com/pricing",
        "terms_url": "https://openai.com/terms",
        "privacy_url": "https://openai.com/privacy",
    },
    "anthropic": {
        "display_name": "Anthropic",
        "website_url": "https://anthropic.com",
        "pricing_url": "https://anthropic.com/pricing",
        "terms_url": "https://anthropic.com/terms",
        "privacy_url": "https://anthropic.com/privacy",
    },
    "mistral": {
        "display_name": "Mistral AI",
        "website_url": "https://mistral.ai",
        "pricing_url": "https://mistral.ai/pricing",
        "terms_url": "https://mistral.ai/terms",
        "privacy_url": "https://mistral.ai/privacy",
    },
}


def _format_model_name(model_id: str) -> str:
    """Convert model ID to human-readable name."""
    # Remove provider prefix if present
    name = model_id.split("/")[-1] if "/" in model_id else model_id

    # Capitalize and format
    name = name.replace("-", " ").replace("_", " ")

    # Special formatting for known patterns
    name = name.replace("gemini ", "Gemini ")
    name = name.replace("gpt ", "GPT-")
    name = name.replace("claude ", "Claude ")

    return name.title()


def _determine_tier(
    input_cost: float | None,
    output_cost: float | None,
) -> str:
    """Determine pricing tier based on costs."""
    if input_cost is None or output_cost is None:
        return "unknown"

    # Cost per million tokens
    avg_cost = ((input_cost or 0) + (output_cost or 0)) / 2 * 1_000_000

    if avg_cost < 0.5:
        return "free"
    elif avg_cost < 5:
        return "standard"
    elif avg_cost < 20:
        return "pro"
    else:
        return "enterprise"


async def fetch_models_from_litellm() -> list[dict[str, Any]]:
    """
    Fetch available models from LiteLLM /v1/model/info endpoint.

    Returns list of model info dictionaries.
    """
    base_url = settings.litellm_api_url.rstrip("/")
    url = f"{base_url}/v1/model/info"

    headers = {"Content-Type": "application/json"}
    if settings.litellm_api_key:
        headers["Authorization"] = f"Bearer {settings.litellm_api_key}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            models = []
            for model_data in data.get("data", []):
                model_info = model_data.get("model_info", {})
                provider = model_info.get("litellm_provider", "unknown")
                provider_meta = PROVIDER_METADATA.get(provider, {})

                # Get costs (per token) and convert to per million tokens
                input_cost_per_token = model_info.get("input_cost_per_token")
                output_cost_per_token = model_info.get("output_cost_per_token")

                input_price = input_cost_per_token * 1_000_000 if input_cost_per_token else None
                output_price = output_cost_per_token * 1_000_000 if output_cost_per_token else None

                # Get context window
                max_input_tokens = model_info.get("max_input_tokens")
                max_tokens = model_info.get("max_tokens")
                context_window = max_input_tokens or max_tokens

                model_id = model_data.get("model_name", "")

                models.append({
                    "id": model_id,
                    "name": _format_model_name(model_id),
                    "provider": provider_meta.get("display_name", provider),
                    "description": None,  # LiteLLM doesn't provide descriptions
                    "context_window": context_window,
                    "input_price": round(input_price, 4) if input_price else None,
                    "output_price": round(output_price, 4) if output_price else None,
                    "tier": _determine_tier(input_cost_per_token, output_cost_per_token),
                    "website_url": provider_meta.get("website_url"),
                    "pricing_url": provider_meta.get("pricing_url"),
                    "terms_url": provider_meta.get("terms_url"),
                    "privacy_url": provider_meta.get("privacy_url"),
                    # Additional capabilities
                    "supports_vision": model_info.get("supports_vision"),
                    "supports_function_calling": model_info.get("supports_function_calling"),
                    "supports_streaming": True,  # Assume all models support streaming
                    "max_output_tokens": model_info.get("max_output_tokens"),
                })

            return models

    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch models from LiteLLM: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching models: {e}")
        return []
