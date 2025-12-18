"""Tests for document service - Unit tests with mocking."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.document import Document, DocumentStatus
from app.schemas.document import DocumentUpdate
from app.services import document as document_service


class TestCreateDocument:
    """Test document creation."""

    @pytest.mark.asyncio
    async def test_create_document_success(self):
        """Test creating a document successfully."""
        mock_db = AsyncMock()
        user_id = uuid.uuid4()

        mock_storage = MagicMock()
        mock_storage.upload = AsyncMock(return_value="uploads/user123/test.pdf")

        with patch("app.services.document.get_storage_service", return_value=mock_storage):
            document = await document_service.create_document(
                db=mock_db,
                user_id=user_id,
                filename="test.pdf",
                file_type="pdf",
                file_size=1024,
                file_content=b"fake pdf content",
            )

            mock_storage.upload.assert_called_once()
            mock_db.add.assert_called_once()
            mock_db.flush.assert_called_once()

            assert document.filename == "test.pdf"
            assert document.file_type == "pdf"
            assert document.status == DocumentStatus.pending


class TestGetDocuments:
    """Test getting documents with pagination."""

    @pytest.mark.asyncio
    async def test_get_documents(self):
        """Test getting paginated documents."""
        mock_db = AsyncMock()
        user_id = uuid.uuid4()

        # Mock count
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 10

        # Mock documents
        mock_docs = [MagicMock(spec=Document) for _ in range(5)]
        mock_docs_result = MagicMock()
        mock_docs_result.scalars.return_value.all.return_value = mock_docs

        mock_db.execute.side_effect = [mock_count_result, mock_docs_result]

        documents, total = await document_service.get_documents(
            db=mock_db,
            user_id=user_id,
            page=1,
            per_page=5,
        )

        assert total == 10
        assert len(documents) == 5

    @pytest.mark.asyncio
    async def test_get_documents_empty(self):
        """Test getting documents when user has none."""
        mock_db = AsyncMock()
        user_id = uuid.uuid4()

        # Mock count = 0
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        # Mock empty documents
        mock_docs_result = MagicMock()
        mock_docs_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_count_result, mock_docs_result]

        documents, total = await document_service.get_documents(
            db=mock_db,
            user_id=user_id,
        )

        assert total == 0
        assert len(documents) == 0


class TestGetDocument:
    """Test getting a single document."""

    @pytest.mark.asyncio
    async def test_get_document_found(self):
        """Test getting an existing document."""
        mock_db = AsyncMock()
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_document = MagicMock(spec=Document)
        mock_document.id = document_id
        mock_document.user_id = user_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_document
        mock_db.execute.return_value = mock_result

        result = await document_service.get_document(
            db=mock_db,
            document_id=document_id,
            user_id=user_id,
        )

        assert result == mock_document

    @pytest.mark.asyncio
    async def test_get_document_not_found(self):
        """Test getting a non-existent document."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await document_service.get_document(
            db=mock_db,
            document_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_document_wrong_user(self):
        """Test that document is not returned for wrong user."""
        mock_db = AsyncMock()

        # Returns None because query filters by user_id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await document_service.get_document(
            db=mock_db,
            document_id=uuid.uuid4(),
            user_id=uuid.uuid4(),  # Different user
        )

        assert result is None


class TestUpdateDocument:
    """Test document updates."""

    @pytest.mark.asyncio
    async def test_update_document_success(self):
        """Test updating a document successfully."""
        mock_db = AsyncMock()
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_document = MagicMock(spec=Document)
        mock_document.id = document_id
        mock_document.user_id = user_id
        mock_document.filename = "old.pdf"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_document
        mock_db.execute.return_value = mock_result

        data = DocumentUpdate(filename="new.pdf")

        result = await document_service.update_document(
            db=mock_db,
            document_id=document_id,
            user_id=user_id,
            data=data,
        )

        assert result.filename == "new.pdf"
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_document_not_found(self):
        """Test updating a non-existent document."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        data = DocumentUpdate(filename="new.pdf")

        result = await document_service.update_document(
            db=mock_db,
            document_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            data=data,
        )

        assert result is None


class TestDeleteDocument:
    """Test document deletion."""

    @pytest.mark.asyncio
    async def test_delete_document_success(self):
        """Test deleting a document successfully."""
        mock_db = AsyncMock()
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_document = MagicMock(spec=Document)
        mock_document.id = document_id
        mock_document.user_id = user_id
        mock_document.file_path = "uploads/user/file.pdf"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_document
        mock_db.execute.return_value = mock_result

        mock_storage = MagicMock()
        mock_storage.delete = AsyncMock()

        mock_vector_store = MagicMock()
        mock_vector_store.delete_by_document = AsyncMock()

        with patch("app.services.document.get_storage_service", return_value=mock_storage):
            with patch("app.services.document.get_vector_store", return_value=mock_vector_store):
                result = await document_service.delete_document(
                    db=mock_db,
                    document_id=document_id,
                    user_id=user_id,
                )

        assert result is True
        mock_vector_store.delete_by_document.assert_called_once()
        mock_storage.delete.assert_called_once()
        mock_db.delete.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self):
        """Test deleting a non-existent document."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await document_service.delete_document(
            db=mock_db,
            document_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
        )

        assert result is False


class TestProcessDocument:
    """Test document processing."""

    @pytest.mark.asyncio
    async def test_process_document_not_found(self):
        """Test processing a non-existent document raises error."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="not found"):
            await document_service.process_document(
                db=mock_db,
                document_id=uuid.uuid4(),
            )

    @pytest.mark.asyncio
    async def test_process_document_empty_chunks(self):
        """Test processing a document with no extractable text."""
        mock_db = AsyncMock()
        document_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_document = MagicMock(spec=Document)
        mock_document.id = document_id
        mock_document.user_id = user_id
        mock_document.file_type = "pdf"
        mock_document.file_path = "uploads/user/empty.pdf"
        mock_document.status = DocumentStatus.pending

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_document
        mock_db.execute.return_value = mock_result

        mock_storage = MagicMock()
        mock_storage.download = AsyncMock(return_value=b"")

        mock_processor = MagicMock()
        mock_processor.process = AsyncMock(return_value=[])  # No chunks

        with patch("app.services.document.get_storage_service", return_value=mock_storage):
            with patch("app.services.document.DocumentProcessor", return_value=mock_processor):
                result = await document_service.process_document(
                    db=mock_db,
                    document_id=document_id,
                )

        assert result.status == DocumentStatus.ready
        assert result.chunk_count == 0


class TestCalculatePages:
    """Test page calculation helper."""

    def test_calculate_pages_exact(self):
        """Test with exact division."""
        assert document_service.calculate_pages(100, 10) == 10

    def test_calculate_pages_with_remainder(self):
        """Test with remainder."""
        assert document_service.calculate_pages(101, 10) == 11

    def test_calculate_pages_small_total(self):
        """Test with total less than per_page."""
        assert document_service.calculate_pages(5, 10) == 1

    def test_calculate_pages_zero_total(self):
        """Test with zero total."""
        assert document_service.calculate_pages(0, 10) == 0

    def test_calculate_pages_zero_per_page(self):
        """Test with zero per_page (edge case)."""
        assert document_service.calculate_pages(100, 0) == 0


class TestDocumentStatus:
    """Test document status enum."""

    def test_document_statuses(self):
        """Test that all expected statuses exist."""
        assert DocumentStatus.pending
        assert DocumentStatus.processing
        assert DocumentStatus.ready
        assert DocumentStatus.error

    def test_status_values(self):
        """Test status string values."""
        assert DocumentStatus.pending.value == "pending"
        assert DocumentStatus.processing.value == "processing"
        assert DocumentStatus.ready.value == "ready"
        assert DocumentStatus.error.value == "error"
