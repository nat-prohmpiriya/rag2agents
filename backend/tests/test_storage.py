"""Tests for storage service path traversal protection."""

import tempfile

import pytest

from app.services.storage import LocalStorageService, PathTraversalError


class TestPathTraversalProtection:
    """Test path traversal protection in storage service."""

    @pytest.fixture
    def storage_service(self):
        """Create a storage service with a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield LocalStorageService(base_path=tmpdir)

    def test_valid_path(self, storage_service):
        """Test that valid paths are allowed."""
        # Simple filename
        path = storage_service._validate_path("file.txt")
        assert path.name == "file.txt"

        # Nested path
        path = storage_service._validate_path("user123/file.txt")
        assert "user123" in str(path)

    def test_path_traversal_blocked(self, storage_service):
        """Test that path traversal attempts are blocked."""
        # Basic path traversal
        with pytest.raises(PathTraversalError):
            storage_service._validate_path("../etc/passwd")

        # Double traversal
        with pytest.raises(PathTraversalError):
            storage_service._validate_path("../../etc/passwd")

        # Hidden traversal
        with pytest.raises(PathTraversalError):
            storage_service._validate_path("subdir/../../../etc/passwd")

        # URL encoded traversal (after decode)
        with pytest.raises(PathTraversalError):
            storage_service._validate_path("..%2F..%2Fetc%2Fpasswd".replace("%2F", "/"))

    def test_absolute_path_blocked(self, storage_service):
        """Test that absolute paths outside base are blocked."""
        with pytest.raises(PathTraversalError):
            storage_service._validate_path("/etc/passwd")

    def test_path_with_dots_in_filename(self, storage_service):
        """Test that legitimate dots in filenames are allowed."""
        # File with dots in name
        path = storage_service._validate_path("file.backup.txt")
        assert path.name == "file.backup.txt"

        # Hidden file (starts with dot)
        path = storage_service._validate_path(".gitignore")
        assert path.name == ".gitignore"

    def test_deeply_nested_valid_path(self, storage_service):
        """Test that deeply nested but valid paths work."""
        path = storage_service._validate_path("a/b/c/d/e/file.txt")
        assert path.name == "file.txt"


class TestStorageOperations:
    """Test storage operations with path validation."""

    @pytest.fixture
    def storage_service(self):
        """Create a storage service with a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = LocalStorageService(base_path=tmpdir)
            yield service, tmpdir

    @pytest.mark.asyncio
    async def test_download_path_traversal_blocked(self, storage_service):
        """Test that download blocks path traversal."""
        service, _ = storage_service
        with pytest.raises(PathTraversalError):
            await service.download("../etc/passwd")

    @pytest.mark.asyncio
    async def test_delete_path_traversal_blocked(self, storage_service):
        """Test that delete blocks path traversal."""
        service, _ = storage_service
        with pytest.raises(PathTraversalError):
            await service.delete("../etc/passwd")

    @pytest.mark.asyncio
    async def test_exists_path_traversal_blocked(self, storage_service):
        """Test that exists blocks path traversal."""
        service, _ = storage_service
        with pytest.raises(PathTraversalError):
            await service.exists("../etc/passwd")
