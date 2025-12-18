"""RAG (Retrieval-Augmented Generation) service."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.telemetry import traced
from app.schemas.vector import ChunkResult
from app.services.embedding import get_embedding_service
from app.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)

# RAG System Prompt Template
RAG_SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on the provided context.

INSTRUCTIONS:
1. Answer the question using ONLY the information from the provided context
2. If the context doesn't contain enough information to answer the question, say "I don't have enough information in the provided documents to answer this question"
3. When citing information, mention the source document name
4. Be concise and accurate
5. Do not make up information that is not in the context

CONTEXT:
{context}

---
Answer the user's question based on the above context."""


@traced()
async def retrieve_context(
    db: AsyncSession,
    query: str,
    user_id: uuid.UUID,
    top_k: int = 5,
    document_ids: list[uuid.UUID] | None = None,
    project_id: uuid.UUID | None = None,
) -> list[ChunkResult]:
    """
    Retrieve relevant document chunks for a query.

    Args:
        db: Database session
        query: User query text
        user_id: User ID for filtering documents
        top_k: Number of chunks to retrieve
        document_ids: Optional list of document IDs to scope the search.
                     If None, search all user's documents.
        project_id: Optional project ID to filter documents in project.
                   If provided, only searches documents assigned to that project.

    Returns:
        List of relevant chunks with scores
    """
    embedding_service = get_embedding_service()
    vector_store = get_vector_store()

    # Generate query embedding
    query_embedding = await embedding_service.embed_query(query)

    # Search for similar chunks
    chunks = await vector_store.search(
        db=db,
        query_embedding=query_embedding,
        top_k=top_k,
        user_id=user_id,
        document_ids=document_ids,
        project_id=project_id,
    )

    scope_info = f"project {project_id}" if project_id else (f"{len(document_ids)} docs" if document_ids else "all")
    logger.info(f"Retrieved {len(chunks)} chunks for query (scoped to {scope_info})")
    return chunks


@traced()
async def build_rag_prompt(
    db: AsyncSession,
    chunks: list[ChunkResult],
) -> str:
    """
    Build RAG system prompt with retrieved context.

    Args:
        db: Database session (for fetching document names)
        chunks: Retrieved chunks

    Returns:
        Formatted system prompt with context
    """
    if not chunks:
        return RAG_SYSTEM_PROMPT.format(context="No relevant documents found.")

    # Import here to avoid circular imports
    from sqlalchemy import select

    from app.models.document import Document

    # Fetch document names for sources
    document_ids = list(set(chunk.document_id for chunk in chunks))
    stmt = select(Document.id, Document.filename).where(Document.id.in_(document_ids))
    result = await db.execute(stmt)
    doc_names = {row.id: row.filename for row in result.all()}

    # Build context string with sources
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        doc_name = doc_names.get(chunk.document_id, "Unknown Document")
        context_parts.append(
            f"[Source {i}: {doc_name}]\n{chunk.content}"
        )

    context = "\n\n".join(context_parts)
    return RAG_SYSTEM_PROMPT.format(context=context)


def format_sources(
    chunks: list[ChunkResult],
    doc_names: dict[uuid.UUID, str],
) -> list[dict]:
    """
    Format chunk results as source information for response.

    Args:
        chunks: Retrieved chunks
        doc_names: Mapping of document IDs to filenames

    Returns:
        List of source info dictionaries
    """
    sources = []

    for chunk in chunks:
        # Truncate content for preview (max 500 chars)
        content_preview = chunk.content[:500] + "..." if len(chunk.content) > 500 else chunk.content
        sources.append({
            "document_id": str(chunk.document_id),
            "filename": doc_names.get(chunk.document_id, "Unknown"),
            "chunk_index": chunk.chunk_index,
            "score": 1 - chunk.score,  # Convert distance to similarity
            "content": content_preview,
        })

    return sources
