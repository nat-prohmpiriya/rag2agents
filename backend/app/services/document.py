"""Document service for managing document lifecycle."""

import logging
import uuid
from math import ceil

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.telemetry import traced
from app.models.chunk import DocumentChunk
from app.models.document import Document, DocumentStatus
from app.schemas.document import DocumentUpdate
from app.schemas.vector import ChunkCreate
from app.services.document_processor import DocumentProcessor
from app.services.embedding import get_embedding_service
from app.services.storage import get_storage_service
from app.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)


@traced()
async def create_document(
    db: AsyncSession,
    user_id: uuid.UUID,
    filename: str,
    file_type: str,
    file_size: int,
    file_content: bytes,
) -> Document:
    """
    Create a new document and upload file to storage.

    Args:
        db: Database session
        user_id: User ID
        filename: Original filename
        file_type: File extension (pdf, docx, txt, md, csv)
        file_size: File size in bytes
        file_content: Raw file bytes

    Returns:
        Created Document instance
    """
    storage = get_storage_service()

    # Upload file to storage
    file_path = await storage.upload(file_content, filename, user_id)

    # Create document record
    document = Document(
        user_id=user_id,
        filename=filename,
        file_type=file_type,
        file_size=file_size,
        file_path=file_path,
        status=DocumentStatus.pending,
    )
    db.add(document)
    await db.flush()

    logger.info(f"Created document {document.id} for user {user_id}")
    return document


@traced()
async def get_documents(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Document], int]:
    """
    Get paginated documents for a user.

    Args:
        db: Database session
        user_id: User ID
        page: Page number (1-indexed)
        per_page: Items per page

    Returns:
        Tuple of (documents list, total count)
    """
    # Count total
    count_stmt = select(func.count(Document.id)).where(Document.user_id == user_id)
    total = (await db.execute(count_stmt)).scalar() or 0

    # Get paginated documents
    offset = (page - 1) * per_page
    stmt = (
        select(Document)
        .where(Document.user_id == user_id)
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    documents = list(result.scalars().all())

    return documents, total


@traced()
async def get_document(
    db: AsyncSession,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Document | None:
    """
    Get a document by ID (with ownership check).

    Args:
        db: Database session
        document_id: Document ID
        user_id: User ID for ownership check

    Returns:
        Document if found and owned by user, None otherwise
    """
    stmt = (
        select(Document)
        .options(selectinload(Document.chunks))
        .where(Document.id == document_id, Document.user_id == user_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


@traced()
async def update_document(
    db: AsyncSession,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
    data: DocumentUpdate,
) -> Document | None:
    """
    Update document metadata.

    Args:
        db: Database session
        document_id: Document ID
        user_id: User ID for ownership check
        data: Update data

    Returns:
        Updated Document if found and owned by user, None otherwise
    """
    document = await get_document(db, document_id, user_id)
    if not document:
        return None

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)

    await db.flush()
    logger.info(f"Updated document {document_id}")
    return document


@traced()
async def delete_document(
    db: AsyncSession,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """
    Delete a document and its associated chunks and file.

    Args:
        db: Database session
        document_id: Document ID
        user_id: User ID for ownership check

    Returns:
        True if deleted, False if not found
    """
    document = await get_document(db, document_id, user_id)
    if not document:
        return False

    storage = get_storage_service()
    vector_store = get_vector_store()

    # Delete chunks from vector store
    await vector_store.delete_by_document(db, document_id)

    # Delete file from storage
    await storage.delete(document.file_path)

    # Delete document (chunks cascade)
    await db.delete(document)
    await db.flush()

    logger.info(f"Deleted document {document_id}")
    return True


@traced()
async def process_document(db: AsyncSession, document_id: uuid.UUID) -> Document:
    """
    Process a document: extract text, chunk, embed, and store vectors.

    Args:
        db: Database session
        document_id: Document ID to process

    Returns:
        Updated Document instance
    """
    # Get document
    stmt = select(Document).where(Document.id == document_id)
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()

    if not document:
        raise ValueError(f"Document {document_id} not found")

    # Update status to processing
    document.status = DocumentStatus.processing
    await db.flush()

    try:
        storage = get_storage_service()
        processor = DocumentProcessor()
        embedding_service = get_embedding_service()
        vector_store = get_vector_store()

        # Download file content
        file_content = await storage.download(document.file_path)

        # Extract and chunk text
        text_chunks = await processor.process(file_content, document.file_type)

        if not text_chunks:
            document.status = DocumentStatus.ready
            document.chunk_count = 0
            await db.flush()
            return document

        # Generate embeddings for all chunks
        chunk_contents = [chunk.content for chunk in text_chunks]
        embeddings = await embedding_service.embed_texts(chunk_contents)

        # Create chunk records with embeddings
        chunks_to_store = [
            ChunkCreate(
                document_id=document_id,
                content=text_chunk.content,
                embedding=embedding,
                chunk_index=text_chunk.metadata.index,
                metadata={
                    "char_start": text_chunk.metadata.char_start,
                    "char_end": text_chunk.metadata.char_end,
                    "page_number": text_chunk.metadata.page_number,
                },
            )
            for text_chunk, embedding in zip(text_chunks, embeddings)
        ]

        # Store chunks in vector store
        await vector_store.add_chunks(db, chunks_to_store)

        # Update document status
        document.status = DocumentStatus.ready
        document.chunk_count = len(chunks_to_store)
        await db.flush()

        logger.info(
            f"Processed document {document_id}: {len(chunks_to_store)} chunks created"
        )

        # Send success notification
        try:
            from app.services import notification as notification_service
            await notification_service.notify_document_processed(
                db=db,
                user_id=document.user_id,
                document_id=document_id,
                document_name=document.filename,
                chunk_count=len(chunks_to_store),
            )
        except Exception as notify_err:
            logger.error(f"Failed to send document processed notification: {notify_err}")

        return document

    except Exception as e:
        document.status = DocumentStatus.error
        document.error_message = str(e)
        await db.flush()
        logger.error(f"Failed to process document {document_id}: {e}")

        # Send failure notification
        try:
            from app.services import notification as notification_service
            await notification_service.notify_document_failed(
                db=db,
                user_id=document.user_id,
                document_id=document_id,
                document_name=document.filename,
                error_message=str(e),
            )
        except Exception as notify_err:
            logger.error(f"Failed to send document failed notification: {notify_err}")

        raise


def calculate_pages(total: int, per_page: int) -> int:
    """Calculate total number of pages."""
    return ceil(total / per_page) if per_page > 0 else 0
