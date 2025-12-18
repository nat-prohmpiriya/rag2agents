"""Image generation API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_context
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.base import BaseResponse
from app.schemas.image import (
    ImageGenerateRequest,
    ImageGenerateResponse,
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
