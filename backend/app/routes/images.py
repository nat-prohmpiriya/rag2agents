"""Image generation API endpoints."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import get_context
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.base import BaseResponse
from app.schemas.image import (
    ImageGenerateRequest,
    ImageGenerateResponse,
    ImageHistoryItem,
    ImageHistoryResponse,
    ImageModelInfo,
    ImageModelsResponse,
    ImageSizeInfo,
    ImageSizesResponse,
)
from app.services import image_generation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/images", tags=["images"])


@router.get("/models")
async def get_models(
    current_user: User = Depends(get_current_user),
) -> BaseResponse[ImageModelsResponse]:
    """Get available image generation models."""
    ctx = get_context()

    models = await image_generation.get_available_models()
    model_infos = [ImageModelInfo(**m) for m in models]

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=ImageModelsResponse(models=model_infos),
    )


@router.get("/sizes")
async def get_sizes(
    current_user: User = Depends(get_current_user),
) -> BaseResponse[ImageSizesResponse]:
    """Get available image sizes."""
    ctx = get_context()

    sizes = await image_generation.get_available_sizes()
    size_infos = [ImageSizeInfo(**s) for s in sizes]

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=ImageSizesResponse(sizes=size_infos),
    )


@router.post("/generate")
async def generate_image(
    request: ImageGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse[ImageGenerateResponse]:
    """
    Generate an image from a text prompt.

    - **prompt**: Text description of the image to generate
    - **model**: Model ID to use (default: imagen-3.0-generate-002)
    - **size**: Image size (default: 1024x1024)
    - **n**: Number of images to generate (1-4)
    """
    ctx = get_context()

    try:
        result = await image_generation.generate_image(
            prompt=request.prompt,
            model=request.model,
            size=request.size,
            n=request.n,
            user_id=current_user.id,
            db=db,
        )

        return BaseResponse(
            trace_id=ctx.trace_id,
            data=ImageGenerateResponse(**result),
        )

    except ValueError as e:
        logger.error(f"Image generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error in image generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during image generation",
        )


@router.get("/history")
async def get_history(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse[ImageHistoryResponse]:
    """
    Get user's generated images history.

    - **limit**: Maximum number of images to return (1-100)
    - **offset**: Number of images to skip
    """
    ctx = get_context()

    images = await image_generation.get_user_images(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    total = await image_generation.get_user_images_count(db=db, user_id=current_user.id)

    history_items = [
        ImageHistoryItem(
            id=str(img.id),
            prompt=img.prompt,
            revised_prompt=img.revised_prompt,
            model=img.model,
            size=img.size,
            image_url=img.image_url,
            file_size=img.file_size,
            created_at=img.created_at,
        )
        for img in images
    ]

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=ImageHistoryResponse(
            images=history_items,
            total=total,
            limit=limit,
            offset=offset,
        ),
    )


@router.delete("/{image_id}")
async def delete_image(
    image_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse[dict]:
    """
    Delete a generated image.

    - **image_id**: UUID of the image to delete
    """
    ctx = get_context()

    deleted = await image_generation.delete_user_image(
        db=db,
        user_id=current_user.id,
        image_id=image_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    return BaseResponse(
        trace_id=ctx.trace_id,
        data={"deleted": True, "id": str(image_id)},
    )
