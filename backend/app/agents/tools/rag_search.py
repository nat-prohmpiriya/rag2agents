"""RAG search tool for retrieving relevant document chunks."""

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.tools.base import BaseTool, ToolResult
from app.services.rag import retrieve_context

logger = logging.getLogger(__name__)


class RAGSearchTool(BaseTool):
    """Tool for searching documents using RAG."""

    name = "rag_search"
    description = "Search through documents to find relevant information for answering questions"

    async def execute(
        self,
        query: str,
        db: AsyncSession,
        user_id: uuid.UUID,
        top_k: int = 5,
        document_ids: list[uuid.UUID] | None = None,
        project_id: uuid.UUID | None = None,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute RAG search.

        Args:
            query: Search query text
            db: Database session
            user_id: User ID for filtering documents
            top_k: Number of results to return
            document_ids: Optional list of document IDs to scope search
            project_id: Optional project ID to scope search

        Returns:
            ToolResult with retrieved chunks
        """
        try:
            chunks = await retrieve_context(
                db=db,
                query=query,
                user_id=user_id,
                top_k=top_k,
                document_ids=document_ids,
                project_id=project_id,
            )

            # Format chunks for response
            results = []
            for chunk in chunks:
                results.append({
                    "document_id": str(chunk.document_id),
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "score": 1 - chunk.score,  # Convert distance to similarity
                })

            return ToolResult(
                success=True,
                data=results,
                metadata={"query": query, "top_k": top_k, "count": len(results)},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"query": query},
            )

    def _get_parameters_schema(self) -> dict[str, Any]:
        """Get parameters schema for RAG search."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant documents",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        }


# Singleton instance
rag_search_tool = RAGSearchTool()
