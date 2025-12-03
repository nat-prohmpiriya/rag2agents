"""Document API endpoints."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import get_context
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.base import BaseResponse, MessageResponse
from app.schemas.document import (
    ChunkSummary,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentResponse,
)
from app.services import document as document_service
from app.services.storage import get_storage_service

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_FILE_TYPES = {"pdf", "docx", "txt", "md", "csv"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("", status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BaseResponse[DocumentResponse]:
    """
    Upload a document and start processing.

    Supported file types: pdf, docx, txt, md, csv
    Max file size: 50MB
    """
    ctx = get_context()

    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    file_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if file_ext not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file_ext}' not allowed. Allowed types: {', '.join(ALLOWED_FILE_TYPES)}",
        )

    # Read file content
    file_content = await file.read()
    file_size = len(file_content)

    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024 * 1024)}MB",
        )

    # Create document
    document = await document_service.create_document(
        db=db,
        user_id=current_user.id,
        filename=file.filename,
        file_type=file_ext,
        file_size=file_size,
        file_content=file_content,
    )

    # Commit transaction before starting background task
    # This ensures the document is visible to the background task's session
    await db.commit()

    # Start background processing
    background_tasks.add_task(
        _process_document_background,
        document.id,
    )

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=DocumentResponse.model_validate(document),
    )


async def _process_document_background(document_id: uuid.UUID) -> None:
    """Background task to process document."""
    from app.core.database import SessionLocal

    async with SessionLocal() as db:
        try:
            await document_service.process_document(db, document_id)
            await db.commit()
        except Exception:
            await db.rollback()
            raise


@router.get("")
async def list_documents(
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BaseResponse[DocumentListResponse]:
    """List user documents with pagination."""
    ctx = get_context()

    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20

    documents, total = await document_service.get_documents(
        db=db,
        user_id=current_user.id,
        page=page,
        per_page=per_page,
    )

    pages = document_service.calculate_pages(total, per_page)

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=DocumentListResponse(
            items=[DocumentResponse.model_validate(doc) for doc in documents],
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        ),
    )


@router.get("/{document_id}")
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BaseResponse[DocumentDetailResponse]:
    """Get document detail with chunks summary."""
    ctx = get_context()

    document = await document_service.get_document(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Build chunks summary
    chunks_summary = [
        ChunkSummary(
            id=chunk.id,
            chunk_index=chunk.chunk_index,
            content_preview=chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
            metadata=chunk.metadata_,
        )
        for chunk in document.chunks
    ]

    # Handle status as enum or string
    status_value = document.status.value if hasattr(document.status, 'value') else document.status

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=DocumentDetailResponse(
            id=document.id,
            filename=document.filename,
            file_type=document.file_type,
            file_size=document.file_size,
            status=status_value,
            chunk_count=document.chunk_count,
            error_message=document.error_message,
            created_at=document.created_at,
            updated_at=document.updated_at,
            chunks=chunks_summary,
        ),
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BaseResponse[MessageResponse]:
    """Delete a document and all its chunks."""
    ctx = get_context()

    deleted = await document_service.delete_document(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
    )

    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=MessageResponse(message="Document deleted successfully"),
    )


# Content type mapping for file types
CONTENT_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
    "md": "text/markdown",
    "csv": "text/csv",
}


@router.get("/{document_id}/file")
async def get_document_file(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Get the raw file content of a document.

    Returns the file with appropriate content type for browser viewing.
    """
    document = await document_service.get_document(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    storage = get_storage_service()

    try:
        file_content = await storage.download(document.file_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail="File not found in storage") from e

    content_type = CONTENT_TYPES.get(document.file_type, "application/octet-stream")

    return Response(
        content=file_content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{document.filename}"',
            "Cache-Control": "private, max-age=3600",
        },
    )
