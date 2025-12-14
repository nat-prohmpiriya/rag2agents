"""Tests for agent service - Unit tests with mocking."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.agent import Agent, AgentSource
from app.schemas.agent import AgentCreate, AgentUpdate
from app.services import agent as agent_service


class TestCreateAgent:
    """Test agent creation."""

    @pytest.mark.asyncio
    async def test_create_agent_success(self):
        """Test creating an agent successfully."""
        mock_db = AsyncMock()
        user_id = uuid.uuid4()

        data = AgentCreate(
            name="Test Agent",
            slug="test-agent",
            description="A test agent",
            system_prompt="You are a helpful assistant.",
            tools=["rag_search", "calculator"],
        )

        agent = await agent_service.create_agent(
            db=mock_db,
            user_id=user_id,
            data=data,
        )

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert agent.name == "Test Agent"
        assert agent.slug == "test-agent"
        assert agent.user_id == user_id

    @pytest.mark.asyncio
    async def test_create_agent_with_project(self):
        """Test creating an agent with project ID."""
        mock_db = AsyncMock()
        user_id = uuid.uuid4()
        project_id = uuid.uuid4()

        data = AgentCreate(
            name="Project Agent",
            slug="project-agent",
            project_id=project_id,
        )

        agent = await agent_service.create_agent(
            db=mock_db,
            user_id=user_id,
            data=data,
        )

        assert agent.project_id == project_id


class TestGetAgentById:
    """Test getting agent by ID."""

    @pytest.mark.asyncio
    async def test_get_agent_found(self):
        """Test getting an existing agent."""
        mock_db = AsyncMock()
        agent_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_agent = MagicMock(spec=Agent)
        mock_agent.id = agent_id
        mock_agent.user_id = user_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_agent
        mock_db.execute.return_value = mock_result

        result = await agent_service.get_agent_by_id(
            db=mock_db,
            agent_id=agent_id,
            user_id=user_id,
        )

        assert result == mock_agent

    @pytest.mark.asyncio
    async def test_get_agent_not_found(self):
        """Test getting a non-existent agent."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await agent_service.get_agent_by_id(
            db=mock_db,
            agent_id=uuid.uuid4(),
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_agent_without_user_filter(self):
        """Test getting agent without user ID filter."""
        mock_db = AsyncMock()
        agent_id = uuid.uuid4()

        mock_agent = MagicMock(spec=Agent)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_agent
        mock_db.execute.return_value = mock_result

        result = await agent_service.get_agent_by_id(
            db=mock_db,
            agent_id=agent_id,
            user_id=None,
        )

        assert result == mock_agent


class TestGetAgentBySlug:
    """Test getting agent by slug."""

    @pytest.mark.asyncio
    async def test_get_agent_by_slug_found(self):
        """Test getting an agent by slug."""
        mock_db = AsyncMock()

        mock_agent = MagicMock(spec=Agent)
        mock_agent.slug = "my-agent"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_agent
        mock_db.execute.return_value = mock_result

        result = await agent_service.get_agent_by_slug(
            db=mock_db,
            slug="my-agent",
        )

        assert result == mock_agent

    @pytest.mark.asyncio
    async def test_get_agent_by_slug_not_found(self):
        """Test getting a non-existent agent by slug."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await agent_service.get_agent_by_slug(
            db=mock_db,
            slug="nonexistent",
        )

        assert result is None


class TestGetUserAgents:
    """Test getting user agents with pagination."""

    @pytest.mark.asyncio
    async def test_get_user_agents(self):
        """Test getting paginated user agents."""
        mock_db = AsyncMock()
        user_id = uuid.uuid4()

        # Mock count
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 10

        # Mock agents
        mock_agents = [MagicMock(spec=Agent) for _ in range(5)]
        mock_agents_result = MagicMock()
        mock_agents_result.scalars.return_value.all.return_value = mock_agents

        mock_db.execute.side_effect = [mock_count_result, mock_agents_result]

        agents, total = await agent_service.get_user_agents(
            db=mock_db,
            user_id=user_id,
            page=1,
            per_page=5,
        )

        assert total == 10
        assert len(agents) == 5

    @pytest.mark.asyncio
    async def test_get_user_agents_empty(self):
        """Test getting agents when user has none."""
        mock_db = AsyncMock()
        user_id = uuid.uuid4()

        # Mock count
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        # Mock empty agents
        mock_agents_result = MagicMock()
        mock_agents_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_count_result, mock_agents_result]

        agents, total = await agent_service.get_user_agents(
            db=mock_db,
            user_id=user_id,
        )

        assert total == 0
        assert len(agents) == 0


class TestUpdateAgent:
    """Test updating agents."""

    @pytest.mark.asyncio
    async def test_update_agent_success(self):
        """Test updating an agent successfully."""
        mock_db = AsyncMock()
        agent_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_agent = MagicMock(spec=Agent)
        mock_agent.id = agent_id
        mock_agent.user_id = user_id
        mock_agent.source = AgentSource.user.value
        mock_agent.name = "Old Name"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_agent
        mock_db.execute.return_value = mock_result

        data = AgentUpdate(name="New Name")

        result = await agent_service.update_agent(
            db=mock_db,
            agent_id=agent_id,
            user_id=user_id,
            data=data,
        )

        assert result.name == "New Name"
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_agent_not_found(self):
        """Test updating a non-existent agent."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        data = AgentUpdate(name="New Name")

        result = await agent_service.update_agent(
            db=mock_db,
            agent_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            data=data,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_update_system_agent_blocked(self):
        """Test that system agents cannot be updated."""
        mock_db = AsyncMock()
        agent_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_agent = MagicMock(spec=Agent)
        mock_agent.id = agent_id
        mock_agent.source = AgentSource.system.value  # System agent

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_agent
        mock_db.execute.return_value = mock_result

        data = AgentUpdate(name="Hacked Name")

        result = await agent_service.update_agent(
            db=mock_db,
            agent_id=agent_id,
            user_id=user_id,
            data=data,
        )

        assert result is None  # Update should be blocked


class TestDeleteAgent:
    """Test deleting agents."""

    @pytest.mark.asyncio
    async def test_delete_agent_success(self):
        """Test deleting an agent successfully."""
        mock_db = AsyncMock()
        agent_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_agent = MagicMock(spec=Agent)
        mock_agent.id = agent_id
        mock_agent.user_id = user_id
        mock_agent.source = AgentSource.user.value

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_agent
        mock_db.execute.return_value = mock_result

        result = await agent_service.delete_agent(
            db=mock_db,
            agent_id=agent_id,
            user_id=user_id,
        )

        assert result is True
        mock_db.delete.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_agent_not_found(self):
        """Test deleting a non-existent agent."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await agent_service.delete_agent(
            db=mock_db,
            agent_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_system_agent_blocked(self):
        """Test that system agents cannot be deleted."""
        mock_db = AsyncMock()
        agent_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_agent = MagicMock(spec=Agent)
        mock_agent.id = agent_id
        mock_agent.source = AgentSource.system.value  # System agent

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_agent
        mock_db.execute.return_value = mock_result

        result = await agent_service.delete_agent(
            db=mock_db,
            agent_id=agent_id,
            user_id=user_id,
        )

        assert result is False  # Delete should be blocked
        mock_db.delete.assert_not_called()


class TestCheckSlugExists:
    """Test slug existence checking."""

    @pytest.mark.asyncio
    async def test_slug_exists_in_db(self):
        """Test checking a slug that exists in database."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid.uuid4()  # Found
        mock_db.execute.return_value = mock_result

        with patch.object(agent_service.agent_loader, "list_agents", return_value=[]):
            result = await agent_service.check_slug_exists(
                db=mock_db,
                slug="existing-slug",
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_slug_exists_in_system(self):
        """Test checking a slug that exists in system agents."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # Not in DB
        mock_db.execute.return_value = mock_result

        system_agents = [{"slug": "system-agent", "name": "System Agent"}]

        with patch.object(agent_service.agent_loader, "list_agents", return_value=system_agents):
            result = await agent_service.check_slug_exists(
                db=mock_db,
                slug="system-agent",
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_slug_not_exists(self):
        """Test checking a slug that doesn't exist."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch.object(agent_service.agent_loader, "list_agents", return_value=[]):
            result = await agent_service.check_slug_exists(
                db=mock_db,
                slug="new-slug",
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_slug_exists_excludes_own_id(self):
        """Test checking slug with exclusion for update."""
        mock_db = AsyncMock()
        own_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # Not found (excluding self)
        mock_db.execute.return_value = mock_result

        with patch.object(agent_service.agent_loader, "list_agents", return_value=[]):
            result = await agent_service.check_slug_exists(
                db=mock_db,
                slug="my-slug",
                exclude_id=own_id,
            )

        assert result is False


class TestGetAllAgentsForUser:
    """Test getting all agents (system + user) for a user."""

    @pytest.mark.asyncio
    async def test_get_all_agents_combined(self):
        """Test getting system and user agents combined."""
        mock_db = AsyncMock()
        user_id = uuid.uuid4()

        # Mock system agents
        system_agents = [
            {"slug": "assistant", "name": "Assistant", "tools": ["search"]},
            {"slug": "coder", "name": "Coder", "tools": ["code"]},
        ]

        # Mock user agent
        mock_user_agent = MagicMock(spec=Agent)
        mock_user_agent.id = uuid.uuid4()
        mock_user_agent.user_id = user_id
        mock_user_agent.name = "My Agent"
        mock_user_agent.slug = "my-agent"
        mock_user_agent.description = "Custom agent"
        mock_user_agent.icon = None
        mock_user_agent.system_prompt = "You are helpful"
        mock_user_agent.tools = ["search"]
        mock_user_agent.config = {}
        mock_user_agent.is_active = True
        mock_user_agent.source = AgentSource.user.value
        mock_user_agent.document_ids = None
        mock_user_agent.project_id = None
        mock_user_agent.created_at = None
        mock_user_agent.updated_at = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_user_agent]
        mock_db.execute.return_value = mock_result

        with patch.object(agent_service.agent_loader, "list_agents", return_value=system_agents):
            agents = await agent_service.get_all_agents_for_user(
                db=mock_db,
                user_id=user_id,
            )

        # Should have 2 system + 1 user = 3 agents
        assert len(agents) == 3
        assert agents[0]["source"] == AgentSource.system.value
        assert agents[1]["source"] == AgentSource.system.value
        assert agents[2]["source"] == AgentSource.user.value
