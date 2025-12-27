"""Integration tests for end-to-end chat flow."""

import pytest
from unittest.mock import AsyncMock, patch

from ai_chat.config import load_config
from ai_chat.providers import StreamChunk
from ai_chat.services import ChatService
from tests.fixtures.openai_responses import mock_streaming_response


class MockHttpxClient:
    """Mock httpx AsyncClient for integration tests."""

    def __init__(self, response_lines):
        self.response_lines = response_lines

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def stream(self, method, url, **kwargs):
        """Return mock streaming response."""
        return MockStreamingResponse(self.response_lines)


class MockStreamingResponse:
    """Mock streaming response."""

    def __init__(self, lines):
        self.lines = lines
        self.status_code = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def aiter_lines(self):
        """Iterate over response lines."""
        for line in self.lines:
            yield line

    async def aread(self):
        """Read response (for error cases)."""
        return b""


@pytest.fixture
def mock_ollama_server():
    """Mock Ollama server that returns canned responses."""

    def create_mock_client(*args, **kwargs):
        return MockHttpxClient(mock_streaming_response())

    return create_mock_client


@pytest.mark.asyncio
async def test_end_to_end_chat_flow(
    valid_config_toml, tmp_config_dir, write_config_file, mock_ollama_server
):
    """Full flow: send message -> receive streamed response."""
    # Setup config
    config_file = write_config_file(valid_config_toml)
    config = load_config(str(config_file))

    # Create chat service
    service = ChatService(config)

    assert service.message_count == 0

    # Mock httpx client
    with patch("httpx.AsyncClient", side_effect=mock_ollama_server):
        # Send message and collect response
        chunks = []
        async for chunk in service.stream_response("Hello, AI!"):
            chunks.append(chunk)

        # Verify chunks received
        assert len(chunks) > 0

        # Verify content
        content = "".join(c.content for c in chunks if c.content)
        assert content == "Hello world!"

        # Verify done marker
        assert chunks[-1].done

        # Verify history
        assert service.message_count == 2

        history = service.get_history()
        assert history[0].role == "user"
        assert history[0].content == "Hello, AI!"
        assert history[1].role == "assistant"
        assert history[1].content == "Hello world!"


@pytest.mark.asyncio
async def test_conversation_maintains_history(
    valid_config_toml, tmp_config_dir, write_config_file, mock_ollama_server
):
    """Multiple messages maintain context."""
    # Setup
    config_file = write_config_file(valid_config_toml)
    config = load_config(str(config_file))
    service = ChatService(config)

    with patch("httpx.AsyncClient", side_effect=mock_ollama_server):
        # First message
        async for _ in service.stream_response("First message"):
            pass

        assert service.message_count == 2

        # Second message
        async for _ in service.stream_response("Second message"):
            pass

        assert service.message_count == 4

        # Verify history order
        history = service.get_history()
        assert history[0].role == "user"
        assert history[0].content == "First message"
        assert history[1].role == "assistant"
        assert history[2].role == "user"
        assert history[2].content == "Second message"
        assert history[3].role == "assistant"


@pytest.mark.asyncio
async def test_clear_history_between_conversations(
    valid_config_toml, tmp_config_dir, write_config_file, mock_ollama_server
):
    """Clearing history starts fresh conversation."""
    # Setup
    config_file = write_config_file(valid_config_toml)
    config = load_config(str(config_file))
    service = ChatService(config)

    with patch("httpx.AsyncClient", side_effect=mock_ollama_server):
        # First conversation
        async for _ in service.stream_response("Message 1"):
            pass

        assert service.message_count == 2

        # Clear
        service.clear_history()
        assert service.message_count == 0

        # New conversation
        async for _ in service.stream_response("Message 2"):
            pass

        assert service.message_count == 2

        # Only new message in history
        history = service.get_history()
        assert len(history) == 2
        assert history[0].content == "Message 2"
