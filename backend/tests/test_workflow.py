"""Tests for workflow service - Unit tests with mocking."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.workflow import ExecutionStatus, Workflow, WorkflowExecution, WorkflowStatus
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate
from app.services import workflow as workflow_service


class TestCreateWorkflow:
    """Test workflow creation."""

    @pytest.mark.asyncio
    async def test_create_workflow_success(self):
        """Test creating a workflow successfully."""
        mock_db = AsyncMock()
        user_id = uuid.uuid4()

        data = WorkflowCreate(
            name="Test Workflow",
            description="A test workflow",
        )

        workflow = await workflow_service.create_workflow(
            db=mock_db,
            user_id=user_id,
            data=data,
        )

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once()

        assert workflow.name == "Test Workflow"
        assert workflow.user_id == user_id
        assert workflow.status == WorkflowStatus.draft.value

    @pytest.mark.asyncio
    async def test_create_workflow_as_template(self):
        """Test creating a workflow as template."""
        mock_db = AsyncMock()
        user_id = uuid.uuid4()

        data = WorkflowCreate(
            name="Template Workflow",
            is_template=True,
        )

        workflow = await workflow_service.create_workflow(
            db=mock_db,
            user_id=user_id,
            data=data,
        )

        assert workflow.is_template is True


class TestGetWorkflow:
    """Test getting a single workflow."""

    @pytest.mark.asyncio
    async def test_get_workflow_found(self):
        """Test getting an existing workflow."""
        mock_db = AsyncMock()
        workflow_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_workflow = MagicMock(spec=Workflow)
        mock_workflow.id = workflow_id
        mock_workflow.user_id = user_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_workflow
        mock_db.execute.return_value = mock_result

        result = await workflow_service.get_workflow(
            db=mock_db,
            workflow_id=workflow_id,
            user_id=user_id,
        )

        assert result == mock_workflow

    @pytest.mark.asyncio
    async def test_get_workflow_not_found(self):
        """Test getting a non-existent workflow."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await workflow_service.get_workflow(
            db=mock_db,
            workflow_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
        )

        assert result is None


class TestGetWorkflows:
    """Test getting workflows with pagination."""

    @pytest.mark.asyncio
    async def test_get_workflows(self):
        """Test getting paginated workflows."""
        mock_db = AsyncMock()
        user_id = uuid.uuid4()

        # Mock count
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 15

        # Mock workflows
        mock_workflows = [MagicMock(spec=Workflow) for _ in range(10)]
        mock_workflows_result = MagicMock()
        mock_workflows_result.scalars.return_value.all.return_value = mock_workflows

        mock_db.execute.side_effect = [mock_count_result, mock_workflows_result]

        workflows, total = await workflow_service.get_workflows(
            db=mock_db,
            user_id=user_id,
            page=1,
            page_size=10,
        )

        assert total == 15
        assert len(workflows) == 10

    @pytest.mark.asyncio
    async def test_get_workflows_empty(self):
        """Test getting workflows when user has none."""
        mock_db = AsyncMock()
        user_id = uuid.uuid4()

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_workflows_result = MagicMock()
        mock_workflows_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_count_result, mock_workflows_result]

        workflows, total = await workflow_service.get_workflows(
            db=mock_db,
            user_id=user_id,
        )

        assert total == 0
        assert len(workflows) == 0


class TestUpdateWorkflow:
    """Test workflow updates."""

    @pytest.mark.asyncio
    async def test_update_workflow_success(self):
        """Test updating a workflow successfully."""
        mock_db = AsyncMock()
        workflow_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_workflow = MagicMock(spec=Workflow)
        mock_workflow.id = workflow_id
        mock_workflow.user_id = user_id
        mock_workflow.name = "Old Name"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_workflow
        mock_db.execute.return_value = mock_result

        data = WorkflowUpdate(name="New Name", description="Updated description")

        result = await workflow_service.update_workflow(
            db=mock_db,
            workflow_id=workflow_id,
            user_id=user_id,
            data=data,
        )

        assert result.name == "New Name"
        assert result.description == "Updated description"
        mock_db.flush.assert_called()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_workflow_not_found(self):
        """Test updating a non-existent workflow."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        data = WorkflowUpdate(name="New Name")

        result = await workflow_service.update_workflow(
            db=mock_db,
            workflow_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            data=data,
        )

        assert result is None


class TestDeleteWorkflow:
    """Test workflow deletion."""

    @pytest.mark.asyncio
    async def test_delete_workflow_success(self):
        """Test deleting a workflow successfully."""
        mock_db = AsyncMock()
        workflow_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_workflow = MagicMock(spec=Workflow)
        mock_workflow.id = workflow_id
        mock_workflow.user_id = user_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_workflow
        mock_db.execute.return_value = mock_result

        result = await workflow_service.delete_workflow(
            db=mock_db,
            workflow_id=workflow_id,
            user_id=user_id,
        )

        assert result is True
        mock_db.delete.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_workflow_not_found(self):
        """Test deleting a non-existent workflow."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await workflow_service.delete_workflow(
            db=mock_db,
            workflow_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
        )

        assert result is False


class TestDuplicateWorkflow:
    """Test workflow duplication."""

    @pytest.mark.asyncio
    async def test_duplicate_workflow_success(self):
        """Test duplicating a workflow successfully."""
        mock_db = AsyncMock()
        workflow_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_original = MagicMock(spec=Workflow)
        mock_original.id = workflow_id
        mock_original.user_id = user_id
        mock_original.name = "Original"
        mock_original.description = "Original description"
        mock_original.nodes = [{"id": "1", "type": "input"}]
        mock_original.edges = []
        mock_original.viewport = {"x": 0, "y": 0, "zoom": 1}
        mock_original.config = {}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_original
        mock_db.execute.return_value = mock_result

        result = await workflow_service.duplicate_workflow(
            db=mock_db,
            workflow_id=workflow_id,
            user_id=user_id,
        )

        assert result.name == "Original (Copy)"
        assert result.status == WorkflowStatus.draft.value
        assert result.is_template is False
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_duplicate_workflow_not_found(self):
        """Test duplicating a non-existent workflow."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await workflow_service.duplicate_workflow(
            db=mock_db,
            workflow_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
        )

        assert result is None


class TestGetExecution:
    """Test getting workflow execution."""

    @pytest.mark.asyncio
    async def test_get_execution_found(self):
        """Test getting an existing execution."""
        mock_db = AsyncMock()
        execution_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_execution = MagicMock(spec=WorkflowExecution)
        mock_execution.id = execution_id
        mock_execution.user_id = user_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_execution
        mock_db.execute.return_value = mock_result

        result = await workflow_service.get_execution(
            db=mock_db,
            execution_id=execution_id,
            user_id=user_id,
        )

        assert result == mock_execution

    @pytest.mark.asyncio
    async def test_get_execution_not_found(self):
        """Test getting a non-existent execution."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await workflow_service.get_execution(
            db=mock_db,
            execution_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
        )

        assert result is None


class TestGetWorkflowExecutions:
    """Test getting workflow executions with pagination."""

    @pytest.mark.asyncio
    async def test_get_workflow_executions(self):
        """Test getting paginated executions."""
        mock_db = AsyncMock()
        workflow_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Mock count
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 5

        # Mock executions
        mock_executions = [MagicMock(spec=WorkflowExecution) for _ in range(5)]
        mock_executions_result = MagicMock()
        mock_executions_result.scalars.return_value.all.return_value = mock_executions

        mock_db.execute.side_effect = [mock_count_result, mock_executions_result]

        executions, total = await workflow_service.get_workflow_executions(
            db=mock_db,
            workflow_id=workflow_id,
            user_id=user_id,
        )

        assert total == 5
        assert len(executions) == 5


class TestCancelExecution:
    """Test execution cancellation."""

    @pytest.mark.asyncio
    async def test_cancel_running_execution(self):
        """Test cancelling a running execution."""
        mock_db = AsyncMock()
        execution_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_execution = MagicMock(spec=WorkflowExecution)
        mock_execution.id = execution_id
        mock_execution.user_id = user_id
        mock_execution.status = ExecutionStatus.running.value

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_execution
        mock_db.execute.return_value = mock_result

        result = await workflow_service.cancel_execution(
            db=mock_db,
            execution_id=execution_id,
            user_id=user_id,
        )

        assert result.status == ExecutionStatus.cancelled.value
        mock_db.flush.assert_called()

    @pytest.mark.asyncio
    async def test_cancel_pending_execution(self):
        """Test cancelling a pending execution."""
        mock_db = AsyncMock()
        execution_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_execution = MagicMock(spec=WorkflowExecution)
        mock_execution.id = execution_id
        mock_execution.user_id = user_id
        mock_execution.status = ExecutionStatus.pending.value

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_execution
        mock_db.execute.return_value = mock_result

        result = await workflow_service.cancel_execution(
            db=mock_db,
            execution_id=execution_id,
            user_id=user_id,
        )

        assert result.status == ExecutionStatus.cancelled.value

    @pytest.mark.asyncio
    async def test_cancel_completed_execution_no_effect(self):
        """Test that cancelling a completed execution has no effect."""
        mock_db = AsyncMock()
        execution_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_execution = MagicMock(spec=WorkflowExecution)
        mock_execution.id = execution_id
        mock_execution.user_id = user_id
        mock_execution.status = ExecutionStatus.completed.value

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_execution
        mock_db.execute.return_value = mock_result

        result = await workflow_service.cancel_execution(
            db=mock_db,
            execution_id=execution_id,
            user_id=user_id,
        )

        # Status should remain completed
        assert result.status == ExecutionStatus.completed.value

    @pytest.mark.asyncio
    async def test_cancel_execution_not_found(self):
        """Test cancelling a non-existent execution."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await workflow_service.cancel_execution(
            db=mock_db,
            execution_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
        )

        assert result is None


class TestExecuteWorkflow:
    """Test workflow execution."""

    @pytest.mark.asyncio
    async def test_execute_workflow_not_found(self):
        """Test executing a non-existent workflow raises error."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="not found"):
            await workflow_service.execute_workflow(
                db=mock_db,
                workflow_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                inputs={},
            )


class TestWorkflowStatus:
    """Test workflow status enum."""

    def test_workflow_statuses(self):
        """Test that all expected statuses exist."""
        assert WorkflowStatus.draft
        assert WorkflowStatus.active
        assert WorkflowStatus.archived

    def test_status_values(self):
        """Test status string values."""
        assert WorkflowStatus.draft.value == "draft"
        assert WorkflowStatus.active.value == "active"
        assert WorkflowStatus.archived.value == "archived"


class TestExecutionStatus:
    """Test execution status enum."""

    def test_execution_statuses(self):
        """Test that all expected statuses exist."""
        assert ExecutionStatus.pending
        assert ExecutionStatus.running
        assert ExecutionStatus.completed
        assert ExecutionStatus.failed
        assert ExecutionStatus.cancelled

    def test_status_values(self):
        """Test status string values."""
        assert ExecutionStatus.pending.value == "pending"
        assert ExecutionStatus.running.value == "running"
        assert ExecutionStatus.completed.value == "completed"
        assert ExecutionStatus.failed.value == "failed"
        assert ExecutionStatus.cancelled.value == "cancelled"
