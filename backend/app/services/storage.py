"""File storage service with abstract interface and implementations."""

import logging
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

import aiofiles
import aiofiles.os

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


# Storage service singleton
_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    """
    Factory function to get storage service instance.

    Returns:
        StorageService instance based on configuration
    """
    global _storage_service

    if _storage_service is None:
        if settings.storage_type == "local":
            _storage_service = LocalStorageService()
        else:
            raise ValueError(f"Unknown storage type: {settings.storage_type}")

    return _storage_service
