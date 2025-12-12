"""Workflow API routes."""

import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import get_context
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.base import BaseResponse
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowExecuteRequest,
    WorkflowExecutionInfo,
    WorkflowExecutionListResponse,
    WorkflowInfo,
    WorkflowListResponse,
    WorkflowUpdate,
)
from app.services import workflow as workflow_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workflows", tags=["workflows"])


# =============================================================================
# Workflow Chat Schema
# =============================================================================


class WorkflowChatRequest(BaseModel):
    """Request schema for workflow chat."""

    message: str
    conversation_id: str | None = None


# =============================================================================
# Workflow CRUD
# =============================================================================


@router.get("")
async def list_workflows(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse[WorkflowListResponse]:
    """List all workflows for the current user."""
    ctx = get_context()

    workflows, total = await workflow_service.get_workflows(
        db, current_user.id, page=page, page_size=page_size
    )

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=WorkflowListResponse(
            workflows=[WorkflowInfo.model_validate(w) for w in workflows],
            total=total,
            page=page,
            page_size=page_size,
        ),
    )


@router.post("")
async def create_workflow(
    data: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse[WorkflowInfo]:
    """Create a new workflow."""
    ctx = get_context()

    workflow = await workflow_service.create_workflow(db, current_user.id, data)

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=WorkflowInfo.model_validate(workflow),
    )


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse[WorkflowInfo]:
    """Get a workflow by ID."""
    ctx = get_context()

    workflow = await workflow_service.get_workflow(db, workflow_id, current_user.id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=WorkflowInfo.model_validate(workflow),
    )


@router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: uuid.UUID,
    data: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse[WorkflowInfo]:
    """Update a workflow."""
    ctx = get_context()

    workflow = await workflow_service.update_workflow(
        db, workflow_id, current_user.id, data
    )
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=WorkflowInfo.model_validate(workflow),
    )


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse[dict]:
    """Delete a workflow."""
    ctx = get_context()

    deleted = await workflow_service.delete_workflow(db, workflow_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return BaseResponse(
        trace_id=ctx.trace_id,
        data={"message": "Workflow deleted successfully"},
    )


@router.post("/{workflow_id}/duplicate")
async def duplicate_workflow(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse[WorkflowInfo]:
    """Duplicate a workflow."""
    ctx = get_context()

    workflow = await workflow_service.duplicate_workflow(db, workflow_id, current_user.id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=WorkflowInfo.model_validate(workflow),
    )


# =============================================================================
# Workflow Execution
# =============================================================================


@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: uuid.UUID,
    data: WorkflowExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse[WorkflowExecutionInfo]:
    """Execute a workflow."""
    ctx = get_context()

    execution = await workflow_service.execute_workflow(
        db, workflow_id, current_user.id, data.inputs
    )

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=WorkflowExecutionInfo.model_validate(execution),
    )


@router.get("/{workflow_id}/executions")
async def list_workflow_executions(
    workflow_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse[WorkflowExecutionListResponse]:
    """List executions for a workflow."""
    ctx = get_context()

    executions, total = await workflow_service.get_workflow_executions(
        db, workflow_id, current_user.id, page=page, page_size=page_size
    )

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=WorkflowExecutionListResponse(
            executions=[WorkflowExecutionInfo.model_validate(e) for e in executions],
            total=total,
            page=page,
            page_size=page_size,
        ),
    )


@router.get("/executions/{execution_id}")
async def get_workflow_execution(
    execution_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse[WorkflowExecutionInfo]:
    """Get a workflow execution by ID."""
    ctx = get_context()

    execution = await workflow_service.get_execution(db, execution_id, current_user.id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=WorkflowExecutionInfo.model_validate(execution),
    )


@router.post("/executions/{execution_id}/cancel")
async def cancel_workflow_execution(
    execution_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BaseResponse[WorkflowExecutionInfo]:
    """Cancel a running workflow execution."""
    ctx = get_context()

    execution = await workflow_service.cancel_execution(db, execution_id, current_user.id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=WorkflowExecutionInfo.model_validate(execution),
    )


# =============================================================================
# Workflow Chat (Interactive)
# =============================================================================


@router.post("/{workflow_id}/chat")
async def workflow_chat_stream(
    workflow_id: uuid.UUID,
    data: WorkflowChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Chat with a workflow using streaming SSE.

    Executes the workflow with the user message as input and streams
    the LLM output in real-time.
    """
    ctx = get_context()
    ctx.user_id = current_user.id

    # Get workflow
    workflow = await workflow_service.get_workflow(db, workflow_id, current_user.id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    async def event_generator():
        try:
            # Execute workflow with streaming
            async for event in workflow_service.execute_workflow_stream(
                db=db,
                workflow_id=workflow_id,
                user_id=current_user.id,
                inputs={"query": data.message, "message": data.message},
            ):
                yield f"data: {json.dumps(event)}\n\n"

        except Exception as e:
            logger.error(f"Workflow chat error: {e}")
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
