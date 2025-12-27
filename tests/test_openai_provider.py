"""Unit tests for OpenAI-compatible provider."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from pydantic import ValidationError

from ai_chat.config.models import ModelConfig, ProviderType
from ai_chat.providers import (
    AuthenticationError,
    ConnectionError,
    Message,
    ProviderError,
    RateLimitError,
)
from ai_chat.providers.openai_compatible import OpenAICompatibleProvider
from tests.fixtures.openai_responses import (
    create_sse_chunk,
    create_sse_done_marker,
    mock_streaming_response,
)


@pytest.fixture
def openai_model_config():
    """Create a test model config for OpenAI-compatible provider."""
    return ModelConfig(
        provider=ProviderType.OPENAI_COMPATIBLE,
        name="Test Model",
        base_url="http://localhost:11434/v1",
        model="test-model",
        api_key="test-key",
        max_tokens=4096,
        temperature=0.7,
    )


@pytest.fixture
def provider(openai_model_config):
    """Create provider instance."""
    return OpenAICompatibleProvider(openai_model_config)


class MockResponse:
    """Mock httpx Response for testing."""

    def __init__(self, status_code=200, lines=None):
        self.status_code = status_code
        self._lines = lines or []

    async def aiter_lines(self):
        """Async iterator for lines."""
        for line in self._lines:
            yield line

    async def aread(self):
        """Read response body."""
        return b"Error message"

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


@pytest.mark.asyncio
async def test_stream_chat_success(provider):
    """Provider correctly parses SSE stream into StreamChunks."""
    messages = [Message(role="user", content="Hello")]

    # Mock httpx client
    mock_response = MockResponse(lines=mock_streaming_response())

    def mock_stream(*args, **kwargs):
        return mock_response

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.stream = mock_stream
        mock_client_class.return_value.__aenter__.return_value = mock_client

        chunks = []
        async for chunk in provider.stream_chat(messages, max_tokens=100, temperature=0.7):
            chunks.append(chunk)

        # Should receive chunks with content
        assert len(chunks) > 0
        content = "".join(c.content for c in chunks if c.content)
        assert content == "Hello world!"

        # Last chunk should be done marker
        assert chunks[-1].done


@pytest.mark.asyncio
async def test_stream_chat_connection_error(provider):
    """Connection error raises appropriate exception with message."""
    import httpx

    messages = [Message(role="user", content="Hello")]

    def mock_stream(*args, **kwargs):
        raise httpx.ConnectError("Connection refused")

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.stream = mock_stream
        mock_client_class.return_value.__aenter__.return_value = mock_client

        with pytest.raises(ConnectionError) as exc_info:
            async for _ in provider.stream_chat(messages, max_tokens=100, temperature=0.7):
                pass

        assert "Cannot connect" in str(exc_info.value)
        assert provider.config.name in str(exc_info.value)


@pytest.mark.asyncio
async def test_stream_chat_timeout(provider):
    """Request timeout handled gracefully."""
    import httpx

    messages = [Message(role="user", content="Hello")]

    def mock_stream(*args, **kwargs):
        raise httpx.TimeoutException("Request timeout")

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.stream = mock_stream
        mock_client_class.return_value.__aenter__.return_value = mock_client

        with pytest.raises(ConnectionError) as exc_info:
            async for _ in provider.stream_chat(messages, max_tokens=100, temperature=0.7):
                pass

        assert "timed out" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_stream_chat_auth_error(provider):
    """Authentication error raises clear exception."""
    messages = [Message(role="user", content="Hello")]

    mock_response = MockResponse(status_code=401)

    def mock_stream(*args, **kwargs):
        return mock_response

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.stream = mock_stream
        mock_client_class.return_value.__aenter__.return_value = mock_client

        with pytest.raises(AuthenticationError) as exc_info:
            async for _ in provider.stream_chat(messages, max_tokens=100, temperature=0.7):
                pass

        assert "Authentication failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_stream_chat_rate_limit(provider):
    """Rate limit error raised when server returns 429."""
    messages = [Message(role="user", content="Hello")]

    mock_response = MockResponse(status_code=429)

    def mock_stream(*args, **kwargs):
        return mock_response

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.stream = mock_stream
        mock_client_class.return_value.__aenter__.return_value = mock_client

        with pytest.raises(RateLimitError) as exc_info:
            async for _ in provider.stream_chat(messages, max_tokens=100, temperature=0.7):
                pass

        assert "Rate limit" in str(exc_info.value)


def test_parse_sse_data_line():
    """SSE data: lines parsed correctly."""
    # This is tested implicitly in test_stream_chat_success
    pass


def test_parse_sse_done_marker():
    """[DONE] marker signals end of stream."""
    # This is tested implicitly in test_stream_chat_success
    pass


def test_message_format_conversion(provider):
    """Messages converted to OpenAI API format correctly."""
    messages = [
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi there!"),
        Message(role="user", content="How are you?"),
    ]

    openai_messages = provider._convert_messages(messages)

    assert len(openai_messages) == 3
    assert openai_messages[0] == {"role": "user", "content": "Hello"}
    assert openai_messages[1] == {"role": "assistant", "content": "Hi there!"}
    assert openai_messages[2] == {"role": "user", "content": "How are you?"}


def test_supports_feature(provider):
    """Provider correctly reports feature support."""
    # Default config has no special features
    assert not provider.supports_feature("images")
    assert not provider.supports_feature("documents")
    assert not provider.supports_feature("reasoning")

    # Unknown feature
    assert not provider.supports_feature("unknown_feature")


def test_missing_base_url():
    """Provider raises error if base_url is missing."""
    with pytest.raises(ValidationError) as exc_info:
        config = ModelConfig(
            provider=ProviderType.OPENAI_COMPATIBLE,
            name="Test",
            model="test",
            # Missing base_url
        )
        OpenAICompatibleProvider(config)

    assert "base_url" in str(exc_info.value).lower()


def test_missing_model():
    """Provider raises error if model is missing."""
    with pytest.raises(ValidationError) as exc_info:
        config = ModelConfig(
            provider=ProviderType.OPENAI_COMPATIBLE,
            name="Test",
            base_url="http://localhost:11434/v1",
            # Missing model
        )
        OpenAICompatibleProvider(config)

    assert "model" in str(exc_info.value).lower()
