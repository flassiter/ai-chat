"""Unit tests for Bedrock provider."""

import pytest
from botocore.exceptions import ClientError, NoCredentialsError
from pydantic import ValidationError
from unittest.mock import Mock, patch, AsyncMock

from ai_chat.config.models import ModelConfig, ProviderType
from ai_chat.providers import (
    AuthenticationError,
    ConnectionError,
    Message,
    ProviderError,
    RateLimitError,
)
from ai_chat.providers.bedrock import BedrockProvider
from tests.fixtures.bedrock_responses import (
    mock_bedrock_stream_response,
    mock_bedrock_single_chunk,
    mock_bedrock_empty_response,
    mock_bedrock_error_response,
)


@pytest.fixture
def bedrock_model_config():
    """Create a test model config for Bedrock provider."""
    return ModelConfig(
        provider=ProviderType.BEDROCK,
        name="Test Claude",
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        region="us-east-1",
        max_tokens=4096,
        temperature=0.7,
    )


@pytest.fixture
def provider(bedrock_model_config):
    """Create provider instance with mocked boto3 client."""
    with patch("boto3.client") as mock_boto_client:
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        provider = BedrockProvider(bedrock_model_config)
        provider.client = mock_client
        yield provider


@pytest.mark.asyncio
async def test_stream_chat_success(provider):
    """Provider correctly parses Bedrock stream into StreamChunks."""
    messages = [Message(role="user", content="Hello")]

    # Mock Bedrock response
    mock_response = mock_bedrock_stream_response()
    provider.client.converse_stream = Mock(return_value=mock_response)

    chunks = []
    async for chunk in provider.stream_chat(messages, max_tokens=100, temperature=0.7):
        chunks.append(chunk)

    # Should receive chunks with content
    assert len(chunks) > 0
    content = "".join(c.content for c in chunks if c.content)
    assert content == "Hello from Bedrock!"

    # Last chunk should be done marker
    assert chunks[-1].done


@pytest.mark.asyncio
async def test_stream_chat_auth_error(provider):
    """Authentication error raises clear exception."""
    messages = [Message(role="user", content="Hello")]

    # Mock authentication error
    error_response = {
        "Error": {
            "Code": "UnrecognizedClientException",
            "Message": "The security token included in the request is invalid.",
        }
    }
    provider.client.converse_stream = Mock(
        side_effect=ClientError(error_response, "converse_stream")
    )

    with pytest.raises(AuthenticationError) as exc_info:
        async for _ in provider.stream_chat(messages, max_tokens=100, temperature=0.7):
            pass

    assert "authentication failed" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_stream_chat_throttling(provider):
    """Throttling error handled with appropriate message."""
    messages = [Message(role="user", content="Hello")]

    # Mock throttling error
    error_response = {
        "Error": {
            "Code": "ThrottlingException",
            "Message": "Rate exceeded",
        }
    }
    provider.client.converse_stream = Mock(
        side_effect=ClientError(error_response, "converse_stream")
    )

    with pytest.raises(RateLimitError) as exc_info:
        async for _ in provider.stream_chat(messages, max_tokens=100, temperature=0.7):
            pass

    assert "rate limit" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_stream_chat_access_denied(provider):
    """Access denied error raises AuthenticationError."""
    messages = [Message(role="user", content="Hello")]

    # Mock access denied error
    error_response = {
        "Error": {
            "Code": "AccessDeniedException",
            "Message": "User is not authorized to perform action",
        }
    }
    provider.client.converse_stream = Mock(
        side_effect=ClientError(error_response, "converse_stream")
    )

    with pytest.raises(AuthenticationError) as exc_info:
        async for _ in provider.stream_chat(messages, max_tokens=100, temperature=0.7):
            pass

    assert "access denied" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_stream_chat_generic_error(provider):
    """Generic Bedrock error raises ProviderError."""
    messages = [Message(role="user", content="Hello")]

    # Mock generic error
    error_response = {
        "Error": {
            "Code": "InternalServerError",
            "Message": "Internal server error",
        }
    }
    provider.client.converse_stream = Mock(
        side_effect=ClientError(error_response, "converse_stream")
    )

    with pytest.raises(ProviderError) as exc_info:
        async for _ in provider.stream_chat(messages, max_tokens=100, temperature=0.7):
            pass

    assert "bedrock error" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_stream_error_event(provider):
    """Error events in stream raise ProviderError."""
    messages = [Message(role="user", content="Hello")]

    # Mock response with error event
    mock_response = mock_bedrock_error_response()
    provider.client.converse_stream = Mock(return_value=mock_response)

    with pytest.raises(ProviderError) as exc_info:
        async for _ in provider.stream_chat(messages, max_tokens=100, temperature=0.7):
            pass

    assert "stream error" in str(exc_info.value).lower()


def test_message_to_bedrock_format(provider):
    """Messages converted to Bedrock converse API format."""
    messages = [
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi there!"),
        Message(role="user", content="How are you?"),
    ]

    bedrock_messages = provider._convert_messages(messages)

    assert len(bedrock_messages) == 3
    assert bedrock_messages[0]["role"] == "user"
    assert bedrock_messages[0]["content"][0]["text"] == "Hello"
    assert bedrock_messages[1]["role"] == "assistant"
    assert bedrock_messages[1]["content"][0]["text"] == "Hi there!"
    assert bedrock_messages[2]["role"] == "user"
    assert bedrock_messages[2]["content"][0]["text"] == "How are you?"


def test_supports_feature_images(provider):
    """Claude models support images."""
    assert provider.supports_feature("images")


def test_supports_feature_documents(provider):
    """Claude models support documents."""
    assert provider.supports_feature("documents")


def test_supports_feature_reasoning():
    """Extended thinking models support reasoning."""
    config = ModelConfig(
        provider=ProviderType.BEDROCK,
        name="Claude Extended",
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0-extended",
        region="us-east-1",
    )

    with patch("boto3.client"):
        provider = BedrockProvider(config)
        assert provider.supports_feature("reasoning")


def test_supports_feature_unknown(provider):
    """Unknown feature returns False."""
    assert not provider.supports_feature("unknown_feature")


def test_missing_model_id():
    """Provider raises error if model_id is missing."""
    with pytest.raises(ValidationError) as exc_info:
        config = ModelConfig(
            provider=ProviderType.BEDROCK,
            name="Test",
            region="us-east-1",
            # Missing model_id
        )
        with patch("boto3.client"):
            BedrockProvider(config)

    assert "model_id" in str(exc_info.value).lower()


def test_region_fallback():
    """Provider uses default region when not specified."""
    config = ModelConfig(
        provider=ProviderType.BEDROCK,
        name="Test",
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        # No region specified
    )

    with patch("boto3.client") as mock_boto_client:
        provider = BedrockProvider(config)

        # Should use default region
        assert provider.region == "us-east-1"
        mock_boto_client.assert_called_once_with(
            "bedrock-runtime",
            region_name="us-east-1",
        )


def test_credentials_error():
    """No credentials error raises AuthenticationError."""
    config = ModelConfig(
        provider=ProviderType.BEDROCK,
        name="Test",
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        region="us-east-1",
    )

    with patch("boto3.client", side_effect=NoCredentialsError()):
        with pytest.raises(AuthenticationError) as exc_info:
            BedrockProvider(config)

        assert "credentials not configured" in str(exc_info.value).lower()
