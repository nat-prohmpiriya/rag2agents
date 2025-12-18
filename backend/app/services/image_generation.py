"""Service for AI image generation using LiteLLM."""

import logging
import uuid
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.generated_image import GeneratedImage
from app.services import minio_storage

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
    db: AsyncSession | None = None,
) -> dict[str, Any]:
    """
    Generate an image using LiteLLM proxy.

    Args:
        prompt: Text description of the image to generate
        model: Model ID to use for generation
        size: Image size (e.g., "1024x1024")
        n: Number of images to generate
        user_id: Optional user ID for tracking
        db: Optional database session for saving history

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
                    revised_prompt = img_data.get("revised_prompt")

                    # Upload to MinIO if configured
                    minio_result = await minio_storage.upload_image_from_base64(
                        base64_data=image_base64,
                        filename=f"{image_id}.png",
                    )

                    if minio_result:
                        # Use MinIO URL
                        image_url = minio_result["url"]
                        file_size = minio_result["file_size"]

                        # Save to database if session provided
                        if db and user_id:
                            generated_image = GeneratedImage(
                                id=uuid.UUID(image_id),
                                user_id=user_id,
                                prompt=prompt,
                                revised_prompt=revised_prompt,
                                model=model,
                                size=size,
                                image_url=image_url,
                                file_size=file_size,
                            )
                            db.add(generated_image)
                            await db.commit()
                            logger.info(f"Saved generated image to DB: {image_id}")
                    else:
                        # Fallback to data URL if MinIO not available
                        image_url = f"data:image/png;base64,{image_base64}"
                        file_size = None

                elif "url" in img_data:
                    image_url = img_data["url"]
                    image_base64 = None
                    file_size = None
                    revised_prompt = img_data.get("revised_prompt")
                else:
                    continue

                images.append({
                    "id": image_id,
                    "url": image_url,
                    "b64_json": image_base64 if not minio_result else None,
                    "revised_prompt": revised_prompt,
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


async def get_user_images(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
) -> list[GeneratedImage]:
    """
    Get user's generated images history.

    Args:
        db: Database session
        user_id: User ID
        limit: Maximum number of images to return
        offset: Number of images to skip

    Returns:
        List of GeneratedImage objects
    """
    stmt = (
        select(GeneratedImage)
        .where(GeneratedImage.user_id == user_id)
        .order_by(GeneratedImage.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_user_images_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Get total count of user's generated images."""
    from sqlalchemy import func

    stmt = select(func.count()).select_from(GeneratedImage).where(GeneratedImage.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar() or 0


async def delete_user_image(
    db: AsyncSession,
    user_id: uuid.UUID,
    image_id: uuid.UUID,
) -> bool:
    """
    Delete a user's generated image.

    Args:
        db: Database session
        user_id: User ID (for authorization)
        image_id: Image ID to delete

    Returns:
        True if deleted, False if not found
    """
    stmt = select(GeneratedImage).where(
        GeneratedImage.id == image_id,
        GeneratedImage.user_id == user_id,
    )
    result = await db.execute(stmt)
    image = result.scalar_one_or_none()

    if not image:
        return False

    # Delete from MinIO if URL is from MinIO
    if settings.minio_endpoint and settings.minio_endpoint in image.image_url:
        # Extract object name from URL
        object_name = image.image_url.split(f"{settings.minio_bucket}/")[-1]
        await minio_storage.delete_image(object_name)

    # Delete from database
    await db.delete(image)
    await db.commit()

    return True
