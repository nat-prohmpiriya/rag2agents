"""File storage service with abstract interface and implementations."""

import logging
import uuid
from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path

import aiofiles
import aiofiles.os
from minio import Minio
from minio.error import S3Error

from app.config import settings
from app.core.telemetry import traced

logger = logging.getLogger(__name__)


class StorageService(ABC):
    """Abstract base class for file storage operations."""

    @abstractmethod
    async def upload(self, file: bytes, filename: str, user_id: uuid.UUID) -> str:
        """
        Upload a file to storage.

        Args:
            file: File content as bytes
            filename: Original filename
            user_id: ID of the user uploading the file

        Returns:
            Storage path where the file was saved
        """
        pass

    @abstractmethod
    async def download(self, path: str) -> bytes:
        """
        Download a file from storage.

        Args:
            path: Storage path of the file

        Returns:
            File content as bytes
        """
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            path: Storage path of the file

        Returns:
            True if file was deleted, False otherwise
        """
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            path: Storage path of the file

        Returns:
            True if file exists, False otherwise
        """
        pass


class PathTraversalError(Exception):
    """Raised when a path traversal attack is detected."""

    pass


class LocalStorageService(StorageService):
    """Local filesystem storage implementation."""

    def __init__(self, base_path: str | None = None):
        """
        Initialize local storage service.

        Args:
            base_path: Base directory for file storage (defaults to settings)
        """
        self.base_path = Path(base_path or settings.storage_local_path).resolve()

    def _validate_path(self, path: str) -> Path:
        """
        Validate that the path is within the base directory.

        Args:
            path: Relative path to validate

        Returns:
            Resolved absolute path

        Raises:
            PathTraversalError: If path attempts to escape base directory
        """
        # Normalize and resolve the full path
        full_path = (self.base_path / path).resolve()

        # Check if the resolved path is within base_path
        try:
            full_path.relative_to(self.base_path)
        except ValueError as err:
            raise PathTraversalError(
                f"Path traversal detected: '{path}' escapes base directory"
            ) from err

        return full_path

    async def _ensure_directory(self, path: Path) -> None:
        """Ensure directory exists, create if not."""
        if not await aiofiles.os.path.exists(path):
            await aiofiles.os.makedirs(path, exist_ok=True)

    @traced()
    async def upload(self, file: bytes, filename: str, user_id: uuid.UUID) -> str:
        """Upload file to local filesystem."""
        # Create path: {base_path}/{user_id}/{uuid}_{filename}
        user_dir = self.base_path / str(user_id)
        await self._ensure_directory(user_dir)

        # Generate unique filename
        file_uuid = uuid.uuid4()
        safe_filename = f"{file_uuid}_{filename}"
        file_path = user_dir / safe_filename

        # Write file
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file)

        # Return relative path from base_path
        return str(file_path.relative_to(self.base_path))

    @traced()
    async def download(self, path: str) -> bytes:
        """Download file from local filesystem."""
        file_path = self._validate_path(path)

        if not await aiofiles.os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {path}")

        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()

    @traced()
    async def delete(self, path: str) -> bool:
        """Delete file from local filesystem."""
        file_path = self._validate_path(path)

        if not await aiofiles.os.path.exists(file_path):
            return False

        await aiofiles.os.remove(file_path)
        return True

    @traced()
    async def exists(self, path: str) -> bool:
        """Check if file exists in local filesystem."""
        file_path = self._validate_path(path)
        return await aiofiles.os.path.exists(file_path)


class MinIOStorageService(StorageService):
    """MinIO (S3-compatible) storage implementation for documents."""

    def __init__(
        self,
        endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        bucket: str | None = None,
        secure: bool | None = None,
    ):
        """
        Initialize MinIO storage service.

        Args:
            endpoint: MinIO server endpoint (defaults to settings.minio_endpoint)
            access_key: Access key (defaults to settings.minio_access_key)
            secret_key: Secret key (defaults to settings.minio_secret_key)
            bucket: Bucket name (defaults to settings.minio_documents_bucket)
            secure: Use HTTPS (defaults to settings.minio_secure)
        """
        self.endpoint = endpoint or settings.minio_endpoint
        self.access_key = access_key or settings.minio_access_key
        self.secret_key = secret_key or settings.minio_secret_key
        self.bucket = bucket or settings.minio_documents_bucket
        self.secure = secure if secure is not None else settings.minio_secure

        if not all([self.endpoint, self.access_key, self.secret_key, self.bucket]):
            raise ValueError(
                "MinIO storage requires minio_endpoint, minio_access_key, "
                "minio_secret_key, and minio_documents_bucket to be configured"
            )

        # Initialize MinIO client (lazy loading, created on first use)
        self._client: Minio | None = None

    def _get_client(self) -> Minio:
        """Get or create MinIO client."""
        if self._client is None:
            self._client = Minio(
                endpoint=self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure,
            )
            logger.info(f"MinIO client initialized for documents: {self.endpoint}/{self.bucket}")
        return self._client

    def _ensure_bucket_exists(self) -> None:
        """Ensure the bucket exists, create if not."""
        client = self._get_client()
        try:
            if not client.bucket_exists(self.bucket):
                client.make_bucket(self.bucket)
                logger.info(f"Created MinIO bucket: {self.bucket}")
        except S3Error as e:
            logger.error(f"Failed to ensure bucket exists: {e}")
            raise

    @traced()
    async def upload(self, file: bytes, filename: str, user_id: uuid.UUID) -> str:
        """Upload file to MinIO."""
        self._ensure_bucket_exists()
        client = self._get_client()

        # Create object path: documents/{user_id}/{uuid}_{filename}
        file_uuid = uuid.uuid4()
        safe_filename = f"{file_uuid}_{filename}"
        object_name = f"documents/{user_id}/{safe_filename}"

        try:
            client.put_object(
                bucket_name=self.bucket,
                object_name=object_name,
                data=BytesIO(file),
                length=len(file),
            )
            logger.info(f"Uploaded file to MinIO: {self.bucket}/{object_name}")
            return object_name
        except S3Error as e:
            logger.error(f"Failed to upload to MinIO: {e}")
            raise

    @traced()
    async def download(self, path: str) -> bytes:
        """Download file from MinIO."""
        client = self._get_client()

        try:
            response = client.get_object(bucket_name=self.bucket, object_name=path)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise FileNotFoundError(f"File not found in MinIO: {path}") from e
            logger.error(f"Failed to download from MinIO: {e}")
            raise

    @traced()
    async def delete(self, path: str) -> bool:
        """Delete file from MinIO."""
        client = self._get_client()

        try:
            client.remove_object(bucket_name=self.bucket, object_name=path)
            logger.info(f"Deleted file from MinIO: {self.bucket}/{path}")
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            logger.error(f"Failed to delete from MinIO: {e}")
            return False

    @traced()
    async def exists(self, path: str) -> bool:
        """Check if file exists in MinIO."""
        client = self._get_client()

        try:
            client.stat_object(bucket_name=self.bucket, object_name=path)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            logger.error(f"Failed to check file existence in MinIO: {e}")
            return False


# Storage service singleton
_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    """
    Factory function to get storage service instance.

    Returns:
        StorageService instance based on configuration

    Note: Creates a new instance each time to ensure env var changes are picked up.
    """
    if settings.storage_type == "local":
        return LocalStorageService()
    elif settings.storage_type == "minio":
        return MinIOStorageService()
    else:
        raise ValueError(f"Unknown storage type: {settings.storage_type}")
