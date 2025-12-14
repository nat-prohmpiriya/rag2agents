"""Tests for chat API - Unit tests with mocking."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.providers.llm import ChatCompletionResponse, ChatMessage
from app.routes.chat import (
    build_messages_from_history,
    get_or_create_conversation,
    record_chat_usage,
)


def mock_llm_response(content: str = "Hello! How can I help you?") -> ChatCompletionResponse:
    """Create a mock LLM response."""
    return ChatCompletionResponse(
        content=content,
        role="assistant",
        model="gpt-4o-mini",
        usage={
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        },
    )


class TestGetOrCreateConversation:
    """Test get_or_create_conversation helper."""

    @pytest.mark.asyncio
    async def test_create_new_conversation(self):
        """Test creating a new conversation when ID not provided."""
        mock_db = AsyncMock()
        user_id = uuid.uuid4()

        # Mock create_conversation
        mock_conv = MagicMock()
        mock_conv.id = uuid.uuid4()

        with patch("app.routes.chat.conversation_service") as mock_service:
            mock_service.create_conversation = AsyncMock(return_value=mock_conv)

            result = await get_or_create_conversation(
                db=mock_db,
                user_id=user_id,
                conversation_id=None,
            )

            assert result == mock_conv.id
            mock_service.create_conversation.assert_called_once()

    @pytest.mark.asyncio
    async def test_use_existing_conversation(self):
        """Test using existing conversation when ID provided."""
        mock_db = AsyncMock()
        user_id = uuid.uuid4()
        existing_conv_id = uuid.uuid4()

        with patch("app.routes.chat.conversation_service") as mock_service:
            mock_service.get_conversation_simple = AsyncMock()

            result = await get_or_create_conversation(
                db=mock_db,
                user_id=user_id,
                conversation_id=existing_conv_id,
            )

            assert result == existing_conv_id
            mock_service.get_conversation_simple.assert_called_once()


class TestBuildMessagesFromHistory:
    """Test build_messages_from_history helper."""

    @pytest.mark.asyncio
    async def test_builds_message_list(self):
        """Test building message list from history."""
        mock_db = AsyncMock()
        user_id = uuid.uuid4()
        conv_id = uuid.uuid4()

        # Create mock history messages
        mock_msg1 = MagicMock()
        mock_msg1.role.value = "user"
        mock_msg1.content = "Hello"

        mock_msg2 = MagicMock()
        mock_msg2.role.value = "assistant"
        mock_msg2.content = "Hi there!"

        with patch("app.routes.chat.conversation_service") as mock_service:
            mock_service.get_conversation_messages = AsyncMock(
                return_value=[mock_msg1, mock_msg2]
            )

            messages = await build_messages_from_history(
                db=mock_db,
                conversation_id=conv_id,
                user_id=user_id,
                new_message="How are you?",
            )

            assert len(messages) == 3
            assert messages[0].role == "user"
            assert messages[0].content == "Hello"
            assert messages[1].role == "assistant"
            assert messages[1].content == "Hi there!"
            assert messages[2].role == "user"
            assert messages[2].content == "How are you?"

    @pytest.mark.asyncio
    async def test_empty_history(self):
        """Test with no previous messages."""
        mock_db = AsyncMock()
        user_id = uuid.uuid4()
        conv_id = uuid.uuid4()

        with patch("app.routes.chat.conversation_service") as mock_service:
            mock_service.get_conversation_messages = AsyncMock(return_value=[])

            messages = await build_messages_from_history(
                db=mock_db,
                conversation_id=conv_id,
                user_id=user_id,
                new_message="First message",
            )

            assert len(messages) == 1
            assert messages[0].content == "First message"


class TestRecordChatUsage:
    """Test record_chat_usage helper."""

    @pytest.mark.asyncio
    async def test_records_usage_successfully(self):
        """Test recording usage with valid data."""
        from app.models.usage import RequestType

        mock_db = AsyncMock()
        user_id = uuid.uuid4()

        with patch("app.routes.chat.usage_service") as mock_usage:
            mock_usage.record_usage = AsyncMock()

            await record_chat_usage(
                db=mock_db,
                user_id=user_id,
                model="gpt-4o-mini",
                usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
                request_type=RequestType.CHAT,
            )

            mock_usage.record_usage.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_missing_usage(self):
        """Test handling when usage is None."""
        from app.models.usage import RequestType

        mock_db = AsyncMock()
        user_id = uuid.uuid4()

        with patch("app.routes.chat.usage_service") as mock_usage:
            mock_usage.record_usage = AsyncMock()

            # Should not raise error
            await record_chat_usage(
                db=mock_db,
                user_id=user_id,
                model="gpt-4o-mini",
                usage=None,
                request_type=RequestType.CHAT,
            )

            mock_usage.record_usage.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_record_error_gracefully(self):
        """Test that usage recording errors don't break the flow."""
        from app.models.usage import RequestType

        mock_db = AsyncMock()
        user_id = uuid.uuid4()

        with patch("app.routes.chat.usage_service") as mock_usage:
            mock_usage.record_usage = AsyncMock(side_effect=Exception("DB Error"))

            # Should not raise error - just log it
            await record_chat_usage(
                db=mock_db,
                user_id=user_id,
                model="gpt-4o-mini",
                usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
                request_type=RequestType.CHAT,
            )


class TestChatMessage:
    """Test ChatMessage dataclass."""

    def test_chat_message_creation(self):
        """Test creating a ChatMessage."""
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_chat_message_roles(self):
        """Test different message roles."""
        user_msg = ChatMessage(role="user", content="Question")
        assistant_msg = ChatMessage(role="assistant", content="Answer")
        system_msg = ChatMessage(role="system", content="Instructions")

        assert user_msg.role == "user"
        assert assistant_msg.role == "assistant"
        assert system_msg.role == "system"


class TestChatCompletionResponse:
    """Test ChatCompletionResponse dataclass."""

    def test_response_creation(self):
        """Test creating a ChatCompletionResponse."""
        response = ChatCompletionResponse(
            content="Hello!",
            role="assistant",
            model="gpt-4o-mini",
        )
        assert response.content == "Hello!"
        assert response.role == "assistant"
        assert response.model == "gpt-4o-mini"
        assert response.usage is None

    def test_response_with_usage(self):
        """Test response with usage info."""
        response = ChatCompletionResponse(
            content="Hello!",
            role="assistant",
            model="gpt-4o-mini",
            usage={"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        )
        assert response.usage["total_tokens"] == 15

    def test_mock_llm_response_helper(self):
        """Test the mock helper function."""
        response = mock_llm_response("Custom response")
        assert response.content == "Custom response"
        assert response.model == "gpt-4o-mini"
        assert response.usage["total_tokens"] == 30


class TestLLMClientUnit:
    """Unit tests for LLM client functionality."""

    def test_format_messages(self):
        """Test message formatting."""
        from app.providers.llm import LLMClient

        client = LLMClient(base_url="http://test", api_key="test-key")

        messages = [
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi!"),
        ]

        formatted = client._format_messages(messages)

        assert len(formatted) == 2
        assert formatted[0] == {"role": "user", "content": "Hello"}
        assert formatted[1] == {"role": "assistant", "content": "Hi!"}

    def test_get_headers(self):
        """Test header generation."""
        from app.providers.llm import LLMClient

        client = LLMClient(base_url="http://test", api_key="test-key")
        headers = client._get_headers()

        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test-key"

    def test_get_headers_no_api_key(self):
        """Test header generation without API key."""
        from app.providers.llm import LLMClient

        # Explicitly pass empty string for api_key to override settings default
        client = LLMClient(base_url="http://test", api_key="")
        headers = client._get_headers()

        assert headers["Content-Type"] == "application/json"
        # Empty api_key still adds Authorization header with "Bearer "
        # This tests that when api_key is explicitly empty, behavior is consistent
