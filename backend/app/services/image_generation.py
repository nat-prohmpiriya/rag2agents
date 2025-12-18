"""Service for AI image generation using LiteLLM."""

import base64
import logging
import uuid
from datetime import datetime
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Available image generation models
IMAGE_MODELS = [
    {
        "id": "gemini/imagen-4.0-generate-001",
        "name": "Imagen 4.0",
        "provider": "Google",
        "description": "Google's latest image generation model",
    },
]

# Available sizes
IMAGE_SIZES = [
    {"value": "1024x1024", "label": "1024 x 1024 (Square)"},
    {"value": "1536x1024", "label": "1536 x 1024 (Landscape)"},
    {"value": "1024x1536", "label": "1024 x 1536 (Portrait)"},
]


async def get_available_models() -> list[dict[str, Any]]:
    """Get list of available image generation models."""
    return IMAGE_MODELS


async def get_available_sizes() -> list[dict[str, str]]:
    """Get list of available image sizes."""
    return IMAGE_SIZES


async def generate_image(
    prompt: str,
    model: str = "imagen-3.0-generate-002",
    size: str = "1024x1024",
    n: int = 1,
    user_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """
    Generate an image using LiteLLM proxy.

    Args:
        prompt: Text description of the image to generate
        model: Model ID to use for generation
        size: Image size (e.g., "1024x1024")
        n: Number of images to generate
        user_id: Optional user ID for tracking

    Returns:
        Dictionary containing generated image data
    """
    base_url = settings.litellm_api_url.rstrip("/")
    url = f"{base_url}/v1/images/generations"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.litellm_api_key}",
    }

    payload = {
        "model": model,
        "prompt": prompt,
        "n": n,
        "size": size,
        "response_format": "b64_json",  # Get base64 encoded image
    }

    if user_id:
        payload["user"] = str(user_id)

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            # Process response
            images = []
            for i, img_data in enumerate(data.get("data", [])):
                image_id = str(uuid.uuid4())

                # Get base64 data or URL
                if "b64_json" in img_data:
                    image_base64 = img_data["b64_json"]
                    image_url = f"data:image/png;base64,{image_base64}"
                elif "url" in img_data:
                    image_url = img_data["url"]
                    image_base64 = None
                else:
                    continue

                images.append({
                    "id": image_id,
                    "url": image_url,
                    "b64_json": image_base64,
                    "revised_prompt": img_data.get("revised_prompt"),
                })

            return {
                "id": str(uuid.uuid4()),
                "created": datetime.utcnow().isoformat(),
                "model": model,
                "prompt": prompt,
                "size": size,
                "images": images,
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error during image generation: {e.response.status_code} - {e.response.text}")
        raise ValueError(f"Image generation failed: {e.response.text}")
    except httpx.TimeoutException:
        logger.error("Timeout during image generation")
        raise ValueError("Image generation timed out. Please try again.")
    except Exception as e:
        logger.error(f"Unexpected error during image generation: {e}")
        raise ValueError(f"Image generation failed: {str(e)}")
