"""Tests for conversation service - Unit tests with mocking."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.services import conversation as conversation_service


class TestConversationServiceUnit:
    """Unit tests for conversation service with mocking."""

    @pytest.mark.asyncio
    async def test_create_conversation(self):
        """Test creating a conversation."""
        mock_db = AsyncMock()
        user_uuid = uuid.uuid4()

        conversation = await conversation_service.create_conversation(
            db=mock_db,
            user_id=user_uuid,
            title="Test Conversation",
        )

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert conversation.user_id == user_uuid
        assert conversation.title == "Test Conversation"

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self):
        """Test getting a non-existent conversation raises NotFoundError."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(NotFoundError):
            await conversation_service.get_conversation(
                db=mock_db,
                conversation_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
            )

    @pytest.mark.asyncio
    async def test_get_conversation_forbidden(self):
        """Test getting another user's conversation raises ForbiddenError."""
        mock_db = AsyncMock()
        user1_uuid = uuid.uuid4()
        user2_uuid = uuid.uuid4()

        # Create mock conversation owned by user1
        mock_conversation = MagicMock(spec=Conversation)
        mock_conversation.user_id = user1_uuid

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conversation
        mock_db.execute.return_value = mock_result

        # Try to access with user2
        with pytest.raises(ForbiddenError):
            await conversation_service.get_conversation(
                db=mock_db,
                conversation_id=uuid.uuid4(),
                user_id=user2_uuid,
            )

    @pytest.mark.asyncio
    async def test_get_conversation_success(self):
        """Test getting a conversation successfully."""
        mock_db = AsyncMock()
        user_uuid = uuid.uuid4()
        conv_id = uuid.uuid4()

        # Create mock conversation
        mock_conversation = MagicMock(spec=Conversation)
        mock_conversation.id = conv_id
        mock_conversation.user_id = user_uuid
        mock_conversation.title = "Test"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conversation
        mock_db.execute.return_value = mock_result

        result = await conversation_service.get_conversation(
            db=mock_db,
            conversation_id=conv_id,
            user_id=user_uuid,
        )

        assert result.id == conv_id

    @pytest.mark.asyncio
    async def test_list_conversations(self):
        """Test listing conversations."""
        mock_db = AsyncMock()
        user_uuid = uuid.uuid4()

        # Mock count result
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 5

        # Mock conversations result
        mock_conversations = [MagicMock(spec=Conversation) for _ in range(5)]
        mock_conv_result = MagicMock()
        mock_conv_result.scalars.return_value.all.return_value = mock_conversations

        # Return different results for count and list queries
        mock_db.execute.side_effect = [mock_count_result, mock_conv_result]

        conversations, total = await conversation_service.list_conversations(
            db=mock_db,
            user_id=user_uuid,
        )

        assert total == 5
        assert len(conversations) == 5

    @pytest.mark.asyncio
    async def test_delete_conversation(self):
        """Test deleting a conversation."""
        mock_db = AsyncMock()
        user_uuid = uuid.uuid4()
        conv_id = uuid.uuid4()

        # Mock get_conversation_simple
        mock_conversation = MagicMock(spec=Conversation)
        mock_conversation.id = conv_id
        mock_conversation.user_id = user_uuid

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conversation
        mock_db.execute.return_value = mock_result

        result = await conversation_service.delete_conversation(
            db=mock_db,
            conversation_id=conv_id,
            user_id=user_uuid,
        )

        assert result is True
        mock_db.delete.assert_called_once()
        mock_db.flush.assert_called_once()


class TestMessageServiceUnit:
    """Unit tests for message-related functions."""

    @pytest.mark.asyncio
    async def test_add_message(self):
        """Test adding a message to conversation."""
        mock_db = AsyncMock()
        conv_id = uuid.uuid4()

        # Mock execute for conversation query (to check title)
        mock_conv = MagicMock(spec=Conversation)
        mock_conv.title = "Existing Title"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conv
        mock_db.execute.return_value = mock_result

        message = await conversation_service.add_message(
            db=mock_db,
            conversation_id=conv_id,
            role="user",
            content="Hello, world!",
        )

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called()
        assert message.role == MessageRole.USER
        assert message.content == "Hello, world!"

    @pytest.mark.asyncio
    async def test_get_message_count(self):
        """Test getting message count for conversation."""
        mock_db = AsyncMock()
        conv_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar.return_value = 10
        mock_db.execute.return_value = mock_result

        count = await conversation_service.get_conversation_message_count(
            db=mock_db,
            conversation_id=conv_id,
        )

        assert count == 10

    @pytest.mark.asyncio
    async def test_get_last_message_preview(self):
        """Test getting last message preview."""
        mock_db = AsyncMock()
        conv_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = "Last message content"
        mock_db.execute.return_value = mock_result

        preview = await conversation_service.get_last_message_preview(
            db=mock_db,
            conversation_id=conv_id,
        )

        assert preview == "Last message content"

    @pytest.mark.asyncio
    async def test_get_last_message_preview_long_content(self):
        """Test that long preview is truncated."""
        mock_db = AsyncMock()
        conv_id = uuid.uuid4()

        long_content = "A" * 200  # Longer than default max_length
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = long_content
        mock_db.execute.return_value = mock_result

        preview = await conversation_service.get_last_message_preview(
            db=mock_db,
            conversation_id=conv_id,
            max_length=100,
        )

        assert len(preview) == 103  # 100 + "..."
        assert preview.endswith("...")


class TestGenerateTitleFromMessage:
    """Test title generation function."""

    def test_short_message(self):
        """Test short message becomes title as-is."""
        title = conversation_service.generate_title_from_message("Hello world")
        assert title == "Hello world"

    def test_long_message_truncated(self):
        """Test long message is truncated."""
        long_message = "This is a very long message that should be truncated to fit the maximum length limit"
        title = conversation_service.generate_title_from_message(long_message, max_length=30)
        assert len(title) <= 33  # 30 + "..."
        assert title.endswith("...")

    def test_whitespace_normalized(self):
        """Test multiple whitespace is normalized."""
        message = "Hello   world\n\nHow are you"
        title = conversation_service.generate_title_from_message(message)
        assert title == "Hello world How are you"
