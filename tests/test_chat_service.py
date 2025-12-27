"""Unit tests for chat service."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from ai_chat.config import Config
from ai_chat.providers import Message, StreamChunk
from ai_chat.services import ChatService


@pytest.fixture
def chat_service(valid_config_toml, tmp_config_dir, write_config_file):
    """Create chat service with test config."""
    config_file = write_config_file(valid_config_toml)

    from ai_chat.config import load_config

    config = load_config(str(config_file))
    return ChatService(config)


def test_add_message_to_history(chat_service):
    """Messages added to conversation history."""
    assert chat_service.message_count == 0

    chat_service.add_message("user", "Hello")
    assert chat_service.message_count == 1

    chat_service.add_message("assistant", "Hi there!")
    assert chat_service.message_count == 2

    history = chat_service.get_history()
    assert len(history) == 2
    assert history[0].role == "user"
    assert history[0].content == "Hello"
    assert history[1].role == "assistant"
    assert history[1].content == "Hi there!"


def test_clear_history(chat_service):
    """Clear removes all messages."""
    chat_service.add_message("user", "Message 1")
    chat_service.add_message("assistant", "Response 1")
    chat_service.add_message("user", "Message 2")

    assert chat_service.message_count == 3

    chat_service.clear_history()

    assert chat_service.message_count == 0
    assert len(chat_service.get_history()) == 0


def test_set_model(chat_service):
    """Model can be changed."""
    initial_model = chat_service.current_model_key

    # Config has "test-model" available
    assert initial_model == "test-model"

    # Set to same model (should work)
    chat_service.set_model("test-model")
    assert chat_service.current_model_key == "test-model"


def test_set_invalid_model(chat_service):
    """Setting invalid model raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        chat_service.set_model("nonexistent-model")

    assert "not found" in str(exc_info.value)
    assert "test-model" in str(exc_info.value)  # Should list available models


def test_get_current_model_config(chat_service):
    """Current model config can be retrieved."""
    config = chat_service.get_current_model_config()

    assert config.name == "Test Model"
    assert config.model == "test"


def test_get_current_model_name(chat_service):
    """Current model name can be retrieved."""
    name = chat_service.get_current_model_name()

    assert name == "Test Model"


@pytest.mark.asyncio
async def test_stream_delegates_to_provider(chat_service):
    """Service delegates streaming to provider."""
    # Mock provider
    mock_provider = AsyncMock()

    async def mock_stream(*args, **kwargs):
        yield StreamChunk(content="Hello")
        yield StreamChunk(content=" world")
        yield StreamChunk(done=True)

    mock_provider.stream_chat = mock_stream

    # Patch provider creation
    with patch.object(chat_service, "_create_provider", return_value=mock_provider):
        chunks = []
        async for chunk in chat_service.stream_response("Test message"):
            chunks.append(chunk)

        # Should have received chunks
        assert len(chunks) == 3
        content = "".join(c.content for c in chunks if c.content)
        assert content == "Hello world"

        # User message should be in history
        assert chat_service.message_count == 2  # user + assistant
        history = chat_service.get_history()
        assert history[0].role == "user"
        assert history[0].content == "Test message"
        assert history[1].role == "assistant"
        assert history[1].content == "Hello world"


@pytest.mark.asyncio
async def test_stream_error_handling(chat_service):
    """Errors during streaming don't corrupt history."""
    initial_count = chat_service.message_count

    # Mock provider that raises error
    mock_provider = AsyncMock()

    async def mock_stream(*args, **kwargs):
        yield StreamChunk(content="Start")
        raise Exception("Test error")

    mock_provider.stream_chat = mock_stream

    # Patch provider creation
    with patch.object(chat_service, "_create_provider", return_value=mock_provider):
        with pytest.raises(Exception) as exc_info:
            async for chunk in chat_service.stream_response("Test"):
                pass

        assert "Test error" in str(exc_info.value)

        # User message added, but no assistant message (since it failed)
        assert chat_service.message_count == initial_count + 1
        history = chat_service.get_history()
        assert history[-1].role == "user"
