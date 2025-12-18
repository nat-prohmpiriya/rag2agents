"""Chat API routes."""

import json
import logging
import time
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.engine import AgentEngine
from app.core.context import get_context
from app.core.dependencies import get_current_user, get_db, require_token_quota
from app.models.usage import RequestType
from app.models.user import User
from app.providers.llm import ChatMessage as LLMChatMessage
from app.providers.llm import ImageContent, llm_client
from app.schemas.base import BaseResponse
from app.schemas.chat import (
    AgentChatResponse,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    SourceInfo,
    UsageInfo,
)
from app.schemas.usage import UsageRecordCreate, get_credits_for_model
from app.services import agent as agent_service
from app.services import conversation as conversation_service
from app.services import rag as rag_service
from app.services import usage as usage_service
from app.services.models import fetch_models_from_litellm
from app.services.quota import check_all_quotas

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


async def record_chat_usage(
    db: AsyncSession,
    user_id: uuid.UUID,
    model: str,
    usage: dict[str, int] | None,
    request_type: RequestType,
    conversation_id: uuid.UUID | None = None,
    message_id: uuid.UUID | None = None,
    agent_id: uuid.UUID | None = None,
    latency_ms: int | None = None,
) -> None:
    """
    Record usage after a chat request completes.

    Args:
        db: Database session
        user_id: User ID
        model: Model used
        usage: Usage info from LLM response
        request_type: Type of request (chat, rag, agent)
        conversation_id: Optional conversation ID
        message_id: Optional message ID
        agent_id: Optional agent ID
        latency_ms: Optional latency in milliseconds
    """
    try:
        tokens_input = usage.get("prompt_tokens", 0) if usage else 0
        tokens_output = usage.get("completion_tokens", 0) if usage else 0
        tokens_total = usage.get("total_tokens", 0) if usage else 0

        # Calculate credits based on model
        credits = get_credits_for_model(model)

        # Create usage record
        record = UsageRecordCreate(
            request_type=request_type,
            model=model,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tokens_total=tokens_total,
            cost=0.0,  # Cost is calculated by LiteLLM, we can sync later
            credits_used=credits,
            latency_ms=latency_ms,
            conversation_id=conversation_id,
            message_id=message_id,
            agent_id=agent_id,
        )

        await usage_service.record_usage(db, user_id, record)
        logger.debug(f"Recorded usage for user {user_id}: model={model}, tokens={tokens_total}, credits={credits}")

    except Exception as e:
        # Don't fail the request if usage recording fails
        logger.error(f"Failed to record usage: {e}")


class ModelInfo(BaseModel):
    """Model information."""
    id: str
    name: str
    provider: str
    description: str | None = None
    context_window: int | None = None
    input_price: float | None = None  # per million tokens
    output_price: float | None = None  # per million tokens
    tier: str | None = None  # "free", "standard", "pro", "enterprise"
    pricing_url: str | None = None
    terms_url: str | None = None
    privacy_url: str | None = None
    website_url: str | None = None
    supports_vision: bool | None = None
    supports_function_calling: bool | None = None
    supports_streaming: bool | None = None
    max_output_tokens: int | None = None


class ModelsResponse(BaseModel):
    """Models list response."""
    models: list[ModelInfo]


@router.get("/models")
async def get_models(
    current_user: User = Depends(get_current_user),
) -> BaseResponse[ModelsResponse]:
    """
    Get available models for chat.

    Fetches model information from LiteLLM proxy.
    Requires authentication.
    """
    ctx = get_context()
    ctx.user_id = current_user.id

    # Fetch models from LiteLLM
    models_data = await fetch_models_from_litellm()

    if not models_data:
        raise HTTPException(
            status_code=503,
            detail="Failed to fetch models from LLM provider"
        )

    # Convert to ModelInfo objects
    models = [ModelInfo(**model) for model in models_data]

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=ModelsResponse(models=models),
    )


async def get_or_create_conversation(
    db: AsyncSession,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID | None,
) -> uuid.UUID:
    """Get existing conversation or create a new one."""
    if conversation_id:
        # Verify the conversation exists and belongs to user
        await conversation_service.get_conversation_simple(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
        )
        return conversation_id
    else:
        # Create a new conversation
        conversation = await conversation_service.create_conversation(
            db=db,
            user_id=user_id,
            title=None,  # Title will be set later or auto-generated
        )
        return conversation.id


async def build_messages_from_history(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    new_message: str,
) -> list[LLMChatMessage]:
    """Build message list from conversation history plus new message."""
    messages: list[LLMChatMessage] = []

    # Get existing messages from conversation
    history = await conversation_service.get_conversation_messages(
        db=db,
        conversation_id=conversation_id,
        user_id=user_id,
    )

    # Add history messages
    for msg in history:
        messages.append(
            LLMChatMessage(role=msg.role.value, content=msg.content)
        )

    # Add new user message
    messages.append(LLMChatMessage(role="user", content=new_message))

    return messages


@router.post("")
async def chat(
    data: ChatRequest,
    current_user: User = Depends(require_token_quota),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse[ChatResponse | AgentChatResponse]:
    """
    Send a chat message and get a response (non-streaming).

    If conversation_id is not provided, a new conversation will be created.
    Messages are saved to the database.
    If agent_slug is provided, uses AgentEngine with tools.

    Requires authentication. Returns 429 if token quota is exceeded.
    """
    ctx = get_context()
    ctx.user_id = current_user.id
    ctx.set_data({
        "action": "chat",
        "model": data.model or llm_client.default_model,
        "message_length": len(data.message),
        "agent_slug": data.agent_slug,
    })

    try:
        # Get or create conversation
        conversation_id = await get_or_create_conversation(
            db=db,
            user_id=current_user.id,
            conversation_id=data.conversation_id,
        )

        # Save user message to DB (skip for regenerate)
        if not data.skip_user_save:
            await conversation_service.add_message(
                db=db,
                conversation_id=conversation_id,
                role="user",
                content=data.message,
            )

        # Build messages list from history
        messages = await build_messages_from_history(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
            new_message=data.message,
        )

        # Remove the last message since we already added it
        messages = messages[:-1]
        messages.append(LLMChatMessage(role="user", content=data.message))

        # If agent_slug is provided, use AgentEngine
        if data.agent_slug:
            # Try to find user agent in DB first
            user_agent = await agent_service.get_agent_by_slug(
                db=db,
                slug=data.agent_slug,
                user_id=current_user.id,
            )

            # Check quota before making agent call
            agent_model = data.model or llm_client.default_model
            credits_needed = get_credits_for_model(agent_model)
            allowed, error_msg = await check_all_quotas(db, current_user.id, credits_needed)
            if not allowed:
                raise HTTPException(status_code=429, detail=error_msg)

            if user_agent:
                # User agent from DB - pass config to engine
                engine = AgentEngine(
                    agent_slug=data.agent_slug,
                    document_ids=user_agent.document_ids,
                    system_prompt=user_agent.system_prompt,
                    tools_list=user_agent.tools,
                    config=user_agent.config,
                )
            else:
                # System agent from YAML
                try:
                    engine = AgentEngine(data.agent_slug)
                except ValueError as e:
                    raise HTTPException(status_code=404, detail=str(e))

            # Process with agent
            start_time = time.time()
            agent_response = await engine.process(
                messages=messages,
                db=db,
                user_id=current_user.id,
            )
            latency_ms = int((time.time() - start_time) * 1000)

            # Save assistant message to DB
            tokens_used = agent_response.usage.get("total_tokens") if agent_response.usage else None
            await conversation_service.add_message(
                db=db,
                conversation_id=conversation_id,
                role="assistant",
                content=agent_response.content,
                tokens_used=tokens_used,
            )

            # Record usage for agent
            await record_chat_usage(
                db=db,
                user_id=current_user.id,
                model=agent_response.model,
                usage=agent_response.usage,
                request_type=RequestType.AGENT,
                conversation_id=conversation_id,
                agent_id=user_agent.id if user_agent else None,
                latency_ms=latency_ms,
            )

            # Build sources from agent response
            sources = None
            if agent_response.sources:
                sources = [
                    SourceInfo(
                        document_id=s.get("document_id", ""),
                        filename=s.get("filename", "Unknown"),
                        chunk_index=s.get("chunk_index", 0),
                        score=s.get("score", 0.0),
                        content=s.get("content", ""),
                    )
                    for s in agent_response.sources
                ]

            # Build agent response
            usage_info = UsageInfo(**agent_response.usage) if agent_response.usage else None
            response_data = AgentChatResponse(
                message=ChatMessage(
                    role="assistant",
                    content=agent_response.content,
                    created_at=datetime.utcnow(),
                ),
                model=agent_response.model,
                usage=usage_info,
                conversation_id=conversation_id,
                sources=sources,
                tools_used=agent_response.tools_used,
                thinking=agent_response.thinking,
                agent_slug=data.agent_slug,
            )

            return BaseResponse(
                trace_id=ctx.trace_id,
                data=response_data,
            )

        # Standard chat flow (no agent)
        # RAG: Retrieve context and build system prompt if enabled
        sources: list[SourceInfo] | None = None
        if data.use_rag:
            chunks = await rag_service.retrieve_context(
                db=db,
                query=data.message,
                user_id=current_user.id,
                top_k=data.rag_top_k,
                document_ids=data.rag_document_ids,
                project_id=data.project_id,
            )
            if chunks:
                # Build RAG system prompt
                rag_prompt = await rag_service.build_rag_prompt(db, chunks)
                # Prepend system message
                messages.insert(0, LLMChatMessage(role="system", content=rag_prompt))
                # Fetch document names for sources
                from sqlalchemy import select

                from app.models.document import Document
                document_ids = list(set(chunk.document_id for chunk in chunks))
                stmt = select(Document.id, Document.filename).where(Document.id.in_(document_ids))
                result = await db.execute(stmt)
                doc_names = {row.id: row.filename for row in result.all()}
                # Build sources list
                sources = [
                    SourceInfo(
                        document_id=str(info["document_id"]),
                        filename=info["filename"],
                        chunk_index=info["chunk_index"],
                        score=info["score"],
                        content=info["content"],
                    )
                    for info in rag_service.format_sources(chunks, doc_names)
                ]

        # Check quota before making LLM call
        model_to_use = data.model or llm_client.default_model
        credits_needed = get_credits_for_model(model_to_use)
        allowed, error_msg = await check_all_quotas(db, current_user.id, credits_needed)
        if not allowed:
            raise HTTPException(status_code=429, detail=error_msg)

        # Call LLM with user_id for usage tracking
        start_time = time.time()
        response = await llm_client.chat_completion(
            messages=messages,
            model=data.model,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
            top_p=data.top_p,
            frequency_penalty=data.frequency_penalty,
            presence_penalty=data.presence_penalty,
            user=str(current_user.id),
        )
        latency_ms = int((time.time() - start_time) * 1000)

        # Save assistant message to DB
        tokens_used = response.usage.get("total_tokens") if response.usage else None
        await conversation_service.add_message(
            db=db,
            conversation_id=conversation_id,
            role="assistant",
            content=response.content,
            tokens_used=tokens_used,
        )

        # Record usage
        request_type = RequestType.RAG if data.use_rag else RequestType.CHAT
        await record_chat_usage(
            db=db,
            user_id=current_user.id,
            model=response.model,
            usage=response.usage,
            request_type=request_type,
            conversation_id=conversation_id,
            latency_ms=latency_ms,
        )

        # Build response
        usage_info = UsageInfo(**response.usage) if response.usage else None
        chat_response = ChatResponse(
            message=ChatMessage(
                role=response.role,
                content=response.content,
                created_at=datetime.utcnow(),
            ),
            model=response.model,
            usage=usage_info,
            conversation_id=conversation_id,
            sources=sources,
        )

        return BaseResponse(
            trace_id=ctx.trace_id,
            data=chat_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.post("/stream")
async def chat_stream(
    data: ChatRequest,
    current_user: User = Depends(require_token_quota),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a chat message and get a streaming response (SSE).

    If conversation_id is not provided, a new conversation will be created.
    Messages are saved to the database.

    Requires authentication. Returns 429 if token quota is exceeded.
    Returns Server-Sent Events with X-Trace-Id header.
    """
    ctx = get_context()
    ctx.user_id = current_user.id
    ctx.set_data({
        "action": "chat_stream",
        "model": data.model or llm_client.default_model,
        "message_length": len(data.message),
    })

    # Get or create conversation before streaming starts
    conversation_id = await get_or_create_conversation(
        db=db,
        user_id=current_user.id,
        conversation_id=data.conversation_id,
    )

    # Save user message to DB (skip for regenerate)
    if not data.skip_user_save:
        await conversation_service.add_message(
            db=db,
            conversation_id=conversation_id,
            role="user",
            content=data.message,
        )

    # Build messages list from history
    messages = await build_messages_from_history(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        new_message=data.message,
    )

    # Remove duplicate user message (only if we saved it above)
    if not data.skip_user_save:
        messages = messages[:-1]

    # Build user message with optional images
    user_images: list[ImageContent] | None = None
    if data.images:
        user_images = [
            ImageContent(media_type=img.media_type, data=img.data)
            for img in data.images
        ]
    messages.append(LLMChatMessage(role="user", content=data.message, images=user_images))

    # RAG: Retrieve context and build system prompt if enabled
    sources_data: list[dict] | None = None
    retrieval_latency_ms: int | None = None
    if data.use_rag:
        retrieval_start = time.time()
        chunks = await rag_service.retrieve_context(
            db=db,
            query=data.message,
            user_id=current_user.id,
            top_k=data.rag_top_k,
            document_ids=data.rag_document_ids,
            project_id=data.project_id,
        )
        if chunks:
            # Build RAG system prompt
            rag_prompt = await rag_service.build_rag_prompt(db, chunks)
            # Prepend system message
            messages.insert(0, LLMChatMessage(role="system", content=rag_prompt))
            # Fetch document names for sources
            from sqlalchemy import select

            from app.models.document import Document
            document_ids = list(set(chunk.document_id for chunk in chunks))
            stmt = select(Document.id, Document.filename).where(Document.id.in_(document_ids))
            result = await db.execute(stmt)
            doc_names = {row.id: row.filename for row in result.all()}
            # Build sources list for streaming response
            sources_data = rag_service.format_sources(chunks, doc_names)
            retrieval_latency_ms = int((time.time() - retrieval_start) * 1000)

    # Get user_id for closure
    user_id_str = str(current_user.id)

    async def event_generator():
        full_response = ""
        llm_start = time.time()
        try:
            # Stream response with user_id for usage tracking
            async for chunk in llm_client.chat_completion_stream(
                messages=messages,
                model=data.model,
                temperature=data.temperature,
                max_tokens=data.max_tokens,
                top_p=data.top_p,
                frequency_penalty=data.frequency_penalty,
                presence_penalty=data.presence_penalty,
                user=user_id_str,
                web_search=data.web_search,
            ):
                full_response += chunk
                # SSE format: data: {"content": "...", "done": false}
                event_data = json.dumps({
                    "content": chunk,
                    "done": False,
                    "conversation_id": str(conversation_id),
                })
                yield f"data: {event_data}\n\n"

            # Calculate LLM latency
            llm_latency_ms = int((time.time() - llm_start) * 1000)

            # Save assistant message after streaming completes
            # Note: We can't get token count from streaming response
            await conversation_service.add_message(
                db=db,
                conversation_id=conversation_id,
                role="assistant",
                content=full_response,
                tokens_used=None,
            )

            # Send done signal with sources and latency data
            done_data = {
                "content": "",
                "done": True,
                "conversation_id": str(conversation_id),
            }
            if sources_data:
                done_data["sources"] = sources_data

            # Add latency data
            done_data["latency"] = {
                "retrieval_ms": retrieval_latency_ms,
                "llm_ms": llm_latency_ms,
            }

            yield f"data: {json.dumps(done_data)}\n\n"

        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            error_data = json.dumps({"error": str(e), "done": True})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "X-Trace-Id": ctx.trace_id,
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
