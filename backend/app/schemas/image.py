"""Schemas for image generation."""

from datetime import datetime

from pydantic import BaseModel, Field


class ImageGenerateRequest(BaseModel):
    """Request schema for image generation."""

    prompt: str = Field(..., min_length=1, max_length=4000, description="Text prompt for image generation")
    model: str = Field(default="imagen-3.0-generate-002", description="Model ID to use")
    size: str = Field(default="1024x1024", description="Image size")
    n: int = Field(default=1, ge=1, le=4, description="Number of images to generate")


class ImageData(BaseModel):
    """Schema for individual generated image."""

    id: str
    url: str
    b64_json: str | None = None
    revised_prompt: str | None = None


class ImageGenerateResponse(BaseModel):
    """Response schema for image generation."""

    id: str
    created: str
    model: str
    prompt: str
    size: str
    images: list[ImageData]


class ImageModelInfo(BaseModel):
    """Schema for image model information."""

    id: str
    name: str
    provider: str
    description: str | None = None


class ImageModelsResponse(BaseModel):
    """Response schema for available image models."""

    models: list[ImageModelInfo]


class ImageSizeInfo(BaseModel):
    """Schema for image size information."""

    value: str
    label: str


class ImageSizesResponse(BaseModel):
    """Response schema for available image sizes."""

    sizes: list[ImageSizeInfo]
