"""Conversation service for managing chat history."""

import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.telemetry import traced
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result data class."""

    conversation_id: uuid.UUID
    title: str | None
    snippet: str
    match_count: int
    rank: float
    created_at: str


@traced()
async def list_conversations(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Conversation], int]:
    """
    List user's conversations with pagination.

    Returns:
        Tuple of (conversations list, total count)
    """
    # Get total count
    count_stmt = (
        select(func.count())
        .select_from(Conversation)
        .where(Conversation.user_id == user_id)
    )
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Get paginated conversations
    offset = (page - 1) * per_page
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    conversations = list(result.scalars().all())

    return conversations, total


async def get_conversation_message_count(
    db: AsyncSession,
    conversation_id: uuid.UUID,
) -> int:
    """Get message count for a conversation."""
    stmt = (
        select(func.count())
        .select_from(Message)
        .where(Message.conversation_id == conversation_id)
    )
    result = await db.execute(stmt)
    return result.scalar() or 0


async def get_last_message_preview(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    max_length: int = 100,
) -> str | None:
    """Get preview of the last message in a conversation."""
    stmt = (
        select(Message.content)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    content = result.scalar_one_or_none()

    if content:
        return content[:max_length] + "..." if len(content) > max_length else content
    return None


@traced()
async def create_conversation(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str | None = None,
    project_id: uuid.UUID | None = None,
) -> Conversation:
    """Create a new conversation."""
    conversation = Conversation(
        user_id=user_id,
        title=title,
        project_id=project_id,
    )
    db.add(conversation)
    await db.flush()
    await db.refresh(conversation)

    logger.info("Conversation created", extra={
        "conversation_id": str(conversation.id),
        "user_id": str(user_id),
        "project_id": str(project_id) if project_id else None,
    })
    return conversation


@traced()
async def get_conversation(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Conversation:
    """
    Get conversation with messages by ID.

    Raises:
        NotFoundError: If conversation not found
        ForbiddenError: If user doesn't own the conversation
    """
    stmt = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise NotFoundError("Conversation not found")

    if conversation.user_id != user_id:
        raise ForbiddenError("You don't have access to this conversation")

    return conversation


async def get_conversation_simple(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Conversation:
    """
    Get conversation by ID without loading messages.

    Raises:
        NotFoundError: If conversation not found
        ForbiddenError: If user doesn't own the conversation
    """
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise NotFoundError("Conversation not found")

    if conversation.user_id != user_id:
        raise ForbiddenError("You don't have access to this conversation")

    return conversation


async def update_conversation(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    title: str | None = None,
) -> Conversation:
    """
    Update conversation title.

    Raises:
        NotFoundError: If conversation not found
        ForbiddenError: If user doesn't own the conversation
    """
    conversation = await get_conversation_simple(db, conversation_id, user_id)

    if title is not None:
        conversation.title = title

    await db.flush()
    await db.refresh(conversation)
    return conversation


@traced()
async def delete_conversation(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """
    Delete a conversation.

    Raises:
        NotFoundError: If conversation not found
        ForbiddenError: If user doesn't own the conversation
    """
    conversation = await get_conversation_simple(db, conversation_id, user_id)
    await db.delete(conversation)
    await db.flush()

    logger.info("Conversation deleted", extra={
        "conversation_id": str(conversation_id),
        "user_id": str(user_id),
    })
    return True


def generate_title_from_message(content: str, max_length: int = 50) -> str:
    """Generate conversation title from first user message."""
    # Remove extra whitespace and newlines
    title = " ".join(content.split())

    if len(title) > max_length:
        return title[:max_length].rstrip() + "..."
    return title


@traced(skip_output=True)  # Skip output to avoid logging large content
async def add_message(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    role: str,
    content: str,
    tokens_used: int | None = None,
) -> Message:
    """Add a message to a conversation."""
    # Convert string role to MessageRole enum
    message_role = MessageRole(role)

    message = Message(
        conversation_id=conversation_id,
        role=message_role,
        content=content,
        tokens_used=tokens_used,
    )
    db.add(message)
    await db.flush()
    await db.refresh(message)

    # Auto-generate title from first user message if not set
    if message_role == MessageRole.USER:
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if conversation and not conversation.title:
            conversation.title = generate_title_from_message(content)
            await db.flush()

    return message


async def get_conversation_messages(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    limit: int | None = None,
) -> list[Message]:
    """
    Get messages for a conversation.

    Raises:
        NotFoundError: If conversation not found
        ForbiddenError: If user doesn't own the conversation
    """
    # Verify ownership first
    await get_conversation_simple(db, conversation_id, user_id)

    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )

    if limit:
        stmt = stmt.limit(limit)

    result = await db.execute(stmt)
    return list(result.scalars().all())


@traced()
async def search_conversations(
    db: AsyncSession,
    user_id: uuid.UUID,
    query: str,
    limit: int = 20,
) -> tuple[list[SearchResult], int]:
    """
    Full-text search conversations by message content.

    Uses PostgreSQL tsvector with GIN index for fast search.
    Returns highlighted snippets with <mark> tags.

    Args:
        db: Database session
        user_id: User ID to filter by
        query: Search query string
        limit: Max results to return

    Returns:
        Tuple of (search results, total count)
    """
    if not query or not query.strip():
        return [], 0

    # Sanitize query for tsquery
    search_terms = query.strip().split()
    tsquery_str = " & ".join(search_terms)

    # Main search query with ts_rank and ts_headline
    search_sql = text("""
        WITH search_results AS (
            SELECT DISTINCT ON (c.id)
                c.id as conversation_id,
                c.title,
                c.created_at,
                ts_headline(
                    'english',
                    m.content,
                    to_tsquery('english', :tsquery),
                    'StartSel=<mark>, StopSel=</mark>, MaxWords=35, MinWords=15, MaxFragments=1'
                ) as snippet,
                ts_rank(m.search_vector, to_tsquery('english', :tsquery)) as rank
            FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            WHERE c.user_id = :user_id
              AND m.search_vector @@ to_tsquery('english', :tsquery)
            ORDER BY c.id, rank DESC
        )
        SELECT
            conversation_id,
            title,
            created_at,
            snippet,
            rank
        FROM search_results
        ORDER BY rank DESC
        LIMIT :limit
    """)

    result = await db.execute(
        search_sql,
        {
            "user_id": str(user_id),
            "tsquery": tsquery_str,
            "limit": limit,
        }
    )
    rows = result.fetchall()

    # Count total matches
    count_sql = text("""
        SELECT COUNT(DISTINCT c.id)
        FROM messages m
        JOIN conversations c ON c.id = m.conversation_id
        WHERE c.user_id = :user_id
          AND m.search_vector @@ to_tsquery('english', :tsquery)
    """)
    count_result = await db.execute(
        count_sql,
        {"user_id": str(user_id), "tsquery": tsquery_str}
    )
    total = count_result.scalar() or 0

    # Count matches per conversation
    match_count_sql = text("""
        SELECT m.conversation_id, COUNT(*) as match_count
        FROM messages m
        JOIN conversations c ON c.id = m.conversation_id
        WHERE c.user_id = :user_id
          AND m.search_vector @@ to_tsquery('english', :tsquery)
        GROUP BY m.conversation_id
    """)
    match_result = await db.execute(
        match_count_sql,
        {"user_id": str(user_id), "tsquery": tsquery_str}
    )
    match_counts = {str(row[0]): row[1] for row in match_result.fetchall()}

    # Build search results
    search_results = []
    for row in rows:
        conv_id = str(row.conversation_id)
        search_results.append(
            SearchResult(
                conversation_id=row.conversation_id,
                title=row.title,
                snippet=row.snippet,
                match_count=match_counts.get(conv_id, 1),
                rank=float(row.rank),
                created_at=row.created_at,
            )
        )

    return search_results, total
