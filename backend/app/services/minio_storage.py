"""MinIO storage service for file uploads."""

import base64
import logging
import uuid
from io import BytesIO

from minio import Minio
from minio.error import S3Error

from app.config import settings

logger = logging.getLogger(__name__)

# MinIO client singleton
_minio_client: Minio | None = None


def get_minio_client() -> Minio | None:
    """Get or create MinIO client."""
    global _minio_client

    if not settings.minio_endpoint:
        logger.warning("MinIO endpoint not configured")
        return None

    if _minio_client is None:
        _minio_client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        logger.info(f"MinIO client initialized: {settings.minio_endpoint}")

    return _minio_client


async def upload_image_from_base64(
    base64_data: str,
    filename: str | None = None,
    content_type: str = "image/png",
) -> dict[str, str | int] | None:
    """
    Upload a base64-encoded image to MinIO.

    Args:
        base64_data: Base64-encoded image data (without data URL prefix)
        filename: Optional filename, will generate UUID if not provided
        content_type: MIME type of the image

    Returns:
        Dictionary with url and file_size, or None if upload failed
    """
    client = get_minio_client()
    if not client:
        logger.error("MinIO client not available")
        return None

    try:
        # Decode base64 data
        image_bytes = base64.b64decode(base64_data)
        file_size = len(image_bytes)

        # Generate filename if not provided
        if not filename:
            ext = "png" if "png" in content_type else "jpg"
            filename = f"{uuid.uuid4()}.{ext}"

        # Create object path with date prefix for organization
        from datetime import datetime
        date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
        object_name = f"generated/{date_prefix}/{filename}"

        # Upload to MinIO
        client.put_object(
            bucket_name=settings.minio_bucket,
            object_name=object_name,
            data=BytesIO(image_bytes),
            length=file_size,
            content_type=content_type,
        )

        # Construct public URL
        protocol = "https" if settings.minio_secure else "http"
        url = f"{protocol}://{settings.minio_endpoint}/{settings.minio_bucket}/{object_name}"

        logger.info(f"Image uploaded to MinIO: {url}")

        return {
            "url": url,
            "file_size": file_size,
            "object_name": object_name,
        }

    except S3Error as e:
        logger.error(f"MinIO S3 error: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to upload image to MinIO: {e}")
        return None


async def delete_image(object_name: str) -> bool:
    """
    Delete an image from MinIO.

    Args:
        object_name: The object name/path in MinIO

    Returns:
        True if deleted successfully, False otherwise
    """
    client = get_minio_client()
    if not client:
        return False

    try:
        client.remove_object(
            bucket_name=settings.minio_bucket,
            object_name=object_name,
        )
        logger.info(f"Image deleted from MinIO: {object_name}")
        return True
    except S3Error as e:
        logger.error(f"Failed to delete image from MinIO: {e}")
        return False
