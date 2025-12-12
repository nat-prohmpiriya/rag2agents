"""Workflow service for managing workflows and executions."""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.telemetry import traced
from app.models.workflow import (
    ExecutionStatus,
    Workflow,
    WorkflowExecution,
    WorkflowStatus,
)
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate

logger = logging.getLogger(__name__)


# =============================================================================
# Workflow CRUD
# =============================================================================


@traced()
async def create_workflow(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: WorkflowCreate,
) -> Workflow:
    """
    Create a new workflow.

    Args:
        db: Database session
        user_id: User ID
        data: Workflow creation data

    Returns:
        Created Workflow instance
    """
    workflow = Workflow(
        user_id=user_id,
        name=data.name,
        description=data.description,
        nodes=[node.model_dump() for node in data.nodes] if data.nodes else [],
        edges=[edge.model_dump() for edge in data.edges] if data.edges else [],
        viewport=data.viewport.model_dump() if data.viewport else {},
        status=WorkflowStatus.draft.value,
        is_template=data.is_template,
        config=data.config or {},
    )
    db.add(workflow)
    await db.flush()
    await db.refresh(workflow)

    logger.info(f"Created workflow {workflow.id} ({workflow.name}) for user {user_id}")
    return workflow


@traced()
async def get_workflow(
    db: AsyncSession,
    workflow_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Workflow | None:
    """
    Get a workflow by ID.

    Args:
        db: Database session
        workflow_id: Workflow ID
        user_id: User ID for ownership check

    Returns:
        Workflow if found, None otherwise
    """
    stmt = select(Workflow).where(
        Workflow.id == workflow_id,
        Workflow.user_id == user_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


@traced()
async def get_workflows(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    status: WorkflowStatus | None = None,
) -> tuple[list[Workflow], int]:
    """
    Get paginated workflows for a user.

    Args:
        db: Database session
        user_id: User ID
        page: Page number (1-indexed)
        page_size: Items per page
        status: Optional status filter

    Returns:
        Tuple of (workflows list, total count)
    """
    # Base query
    base_query = select(Workflow).where(Workflow.user_id == user_id)
    if status:
        base_query = base_query.where(Workflow.status == status.value)

    # Count total
    count_stmt = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Get paginated
    offset = (page - 1) * page_size
    stmt = base_query.order_by(Workflow.updated_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    workflows = list(result.scalars().all())

    return workflows, total


@traced()
async def update_workflow(
    db: AsyncSession,
    workflow_id: uuid.UUID,
    user_id: uuid.UUID,
    data: WorkflowUpdate,
) -> Workflow | None:
    """
    Update a workflow.

    Args:
        db: Database session
        workflow_id: Workflow ID
        user_id: User ID for ownership check
        data: Workflow update data

    Returns:
        Updated Workflow if found, None otherwise
    """
    workflow = await get_workflow(db, workflow_id, user_id)
    if not workflow:
        return None

    if data.name is not None:
        workflow.name = data.name
    if data.description is not None:
        workflow.description = data.description
    if data.nodes is not None:
        workflow.nodes = [node.model_dump() for node in data.nodes]
    if data.edges is not None:
        workflow.edges = [edge.model_dump() for edge in data.edges]
    if data.viewport is not None:
        workflow.viewport = data.viewport.model_dump()
    if data.status is not None:
        workflow.status = data.status.value
    if data.is_template is not None:
        workflow.is_template = data.is_template
    if data.config is not None:
        workflow.config = data.config

    await db.flush()
    await db.refresh(workflow)

    logger.info(f"Updated workflow {workflow_id}")
    return workflow


@traced()
async def delete_workflow(
    db: AsyncSession,
    workflow_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """
    Delete a workflow.

    Args:
        db: Database session
        workflow_id: Workflow ID
        user_id: User ID for ownership check

    Returns:
        True if deleted, False if not found
    """
    workflow = await get_workflow(db, workflow_id, user_id)
    if not workflow:
        return False

    await db.delete(workflow)
    await db.flush()

    logger.info(f"Deleted workflow {workflow_id}")
    return True


@traced()
async def duplicate_workflow(
    db: AsyncSession,
    workflow_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Workflow | None:
    """
    Duplicate a workflow.

    Args:
        db: Database session
        workflow_id: Workflow ID to duplicate
        user_id: User ID

    Returns:
        New Workflow if original found, None otherwise
    """
    original = await get_workflow(db, workflow_id, user_id)
    if not original:
        return None

    # Create copy
    workflow = Workflow(
        user_id=user_id,
        name=f"{original.name} (Copy)",
        description=original.description,
        nodes=original.nodes,
        edges=original.edges,
        viewport=original.viewport,
        status=WorkflowStatus.draft.value,
        is_template=False,
        config=original.config,
    )
    db.add(workflow)
    await db.flush()
    await db.refresh(workflow)

    logger.info(f"Duplicated workflow {workflow_id} to {workflow.id}")
    return workflow


# =============================================================================
# Workflow Execution
# =============================================================================


@traced()
async def execute_workflow(
    db: AsyncSession,
    workflow_id: uuid.UUID,
    user_id: uuid.UUID,
    inputs: dict,
) -> WorkflowExecution:
    """
    Execute a workflow.

    Args:
        db: Database session
        workflow_id: Workflow ID to execute
        user_id: User ID
        inputs: Execution inputs

    Returns:
        WorkflowExecution instance
    """
    from app.services.workflow_engine import WorkflowEngine

    # Get workflow
    workflow = await get_workflow(db, workflow_id, user_id)
    if not workflow:
        raise ValueError(f"Workflow not found: {workflow_id}")

    # Create execution record
    execution = WorkflowExecution(
        workflow_id=workflow_id,
        user_id=user_id,
        status=ExecutionStatus.pending.value,
        inputs=inputs,
        outputs={},
        node_states={},
        logs=[],
        started_at=datetime.now(UTC).isoformat(),
    )
    db.add(execution)
    await db.flush()
    await db.refresh(execution)

    # Execute workflow
    engine = WorkflowEngine(workflow, execution, db)
    try:
        execution.status = ExecutionStatus.running.value
        await db.flush()

        result = await engine.execute(inputs)

        execution.status = ExecutionStatus.completed.value
        execution.outputs = result.get("outputs", {})
        execution.node_states = result.get("node_states", {})
        execution.logs = result.get("logs", [])
        execution.total_tokens = result.get("total_tokens", 0)
        execution.completed_at = datetime.now(UTC).isoformat()

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        execution.status = ExecutionStatus.failed.value
        execution.error_message = str(e)
        execution.completed_at = datetime.now(UTC).isoformat()

    await db.flush()
    await db.refresh(execution)

    return execution


@traced()
async def get_execution(
    db: AsyncSession,
    execution_id: uuid.UUID,
    user_id: uuid.UUID,
) -> WorkflowExecution | None:
    """
    Get a workflow execution by ID.

    Args:
        db: Database session
        execution_id: Execution ID
        user_id: User ID for ownership check

    Returns:
        WorkflowExecution if found, None otherwise
    """
    stmt = select(WorkflowExecution).where(
        WorkflowExecution.id == execution_id,
        WorkflowExecution.user_id == user_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


@traced()
async def get_workflow_executions(
    db: AsyncSession,
    workflow_id: uuid.UUID,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[WorkflowExecution], int]:
    """
    Get paginated executions for a workflow.

    Args:
        db: Database session
        workflow_id: Workflow ID
        user_id: User ID for ownership check
        page: Page number (1-indexed)
        page_size: Items per page

    Returns:
        Tuple of (executions list, total count)
    """
    # Base query
    base_query = select(WorkflowExecution).where(
        WorkflowExecution.workflow_id == workflow_id,
        WorkflowExecution.user_id == user_id,
    )

    # Count total
    count_stmt = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Get paginated
    offset = (page - 1) * page_size
    stmt = base_query.order_by(WorkflowExecution.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    executions = list(result.scalars().all())

    return executions, total


@traced()
async def cancel_execution(
    db: AsyncSession,
    execution_id: uuid.UUID,
    user_id: uuid.UUID,
) -> WorkflowExecution | None:
    """
    Cancel a running workflow execution.

    Args:
        db: Database session
        execution_id: Execution ID
        user_id: User ID for ownership check

    Returns:
        Updated WorkflowExecution if found and running, None otherwise
    """
    execution = await get_execution(db, execution_id, user_id)
    if not execution:
        return None

    if execution.status not in [ExecutionStatus.pending.value, ExecutionStatus.running.value]:
        logger.warning(f"Cannot cancel execution {execution_id} with status {execution.status}")
        return execution

    execution.status = ExecutionStatus.cancelled.value
    execution.completed_at = datetime.now(UTC).isoformat()

    await db.flush()
    await db.refresh(execution)

    logger.info(f"Cancelled execution {execution_id}")
    return execution


# =============================================================================
# Workflow Streaming Execution
# =============================================================================


async def execute_workflow_stream(
    db: AsyncSession,
    workflow_id: uuid.UUID,
    user_id: uuid.UUID,
    inputs: dict,
):
    """
    Execute a workflow with streaming output.

    Yields SSE events as the workflow executes, streaming LLM responses
    in real-time.

    Args:
        db: Database session
        workflow_id: Workflow ID to execute
        user_id: User ID
        inputs: Execution inputs

    Yields:
        Dict events with content, node info, and done status
    """
    from app.services.workflow_engine import WorkflowEngineStream

    # Get workflow
    workflow = await get_workflow(db, workflow_id, user_id)
    if not workflow:
        yield {"error": "Workflow not found", "done": True}
        return

    # Create execution record
    execution = WorkflowExecution(
        workflow_id=workflow_id,
        user_id=user_id,
        status=ExecutionStatus.pending.value,
        inputs=inputs,
        outputs={},
        node_states={},
        logs=[],
        started_at=datetime.now(UTC).isoformat(),
    )
    db.add(execution)
    await db.flush()
    await db.refresh(execution)

    # Execute with streaming
    engine = WorkflowEngineStream(workflow, execution, db)
    try:
        execution.status = ExecutionStatus.running.value
        await db.flush()

        async for event in engine.execute_stream(inputs):
            yield event

        # Update execution after completion
        execution.status = ExecutionStatus.completed.value
        execution.outputs = engine.state.get("node_outputs", {})
        execution.node_states = engine.state.get("node_outputs", {})
        execution.logs = engine.logs
        execution.total_tokens = engine.total_tokens
        execution.completed_at = datetime.now(UTC).isoformat()

    except Exception as e:
        logger.error(f"Workflow streaming execution failed: {e}")
        execution.status = ExecutionStatus.failed.value
        execution.error_message = str(e)
        execution.completed_at = datetime.now(UTC).isoformat()
        yield {"error": str(e), "done": True}

    await db.flush()
