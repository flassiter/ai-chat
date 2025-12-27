"""Unit tests for provider factory."""

import pytest
from unittest.mock import patch

from ai_chat.config.models import ModelConfig, ProviderType
from ai_chat.providers import create_provider
from ai_chat.providers.bedrock import BedrockProvider
from ai_chat.providers.openai_compatible import OpenAICompatibleProvider


def test_create_openai_provider():
    """Factory creates OpenAI-compatible provider for openai_compatible type."""
    config = ModelConfig(
        provider=ProviderType.OPENAI_COMPATIBLE,
        name="Test Ollama",
        base_url="http://localhost:11434/v1",
        model="llama2",
        max_tokens=2048,
        temperature=0.7,
    )

    provider = create_provider(config)

    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.config == config


def test_create_bedrock_provider():
    """Factory creates Bedrock provider for bedrock type."""
    config = ModelConfig(
        provider=ProviderType.BEDROCK,
        name="Claude",
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        region="us-east-1",
        max_tokens=4096,
        temperature=0.7,
    )

    with patch("boto3.client"):
        provider = create_provider(config)

        assert isinstance(provider, BedrockProvider)
        assert provider.config == config


def test_invalid_provider_type():
    """Unknown provider type raises ValueError."""
    # Create a config with an invalid provider type
    # We can't use ProviderType enum for this, so we'll test the error message

    config = ModelConfig(
        provider=ProviderType.OPENAI_COMPATIBLE,
        name="Test",
        base_url="http://localhost:11434/v1",
        model="test",
    )

    # Temporarily change the provider to an invalid value
    config.provider = "invalid_type"  # type: ignore

    with pytest.raises(ValueError) as exc_info:
        create_provider(config)

    assert "unknown provider type" in str(exc_info.value).lower()


def test_factory_preserves_config():
    """Factory preserves all config fields."""
    config = ModelConfig(
        provider=ProviderType.OPENAI_COMPATIBLE,
        name="Custom Model",
        base_url="http://custom:8000/v1",
        model="custom-model",
        api_key="secret-key",
        max_tokens=1000,
        temperature=0.5,
        supports_images=True,
        supports_documents=False,
    )

    provider = create_provider(config)

    assert provider.config.name == "Custom Model"
    assert provider.config.base_url == "http://custom:8000/v1"
    assert provider.config.model == "custom-model"
    assert provider.config.max_tokens == 1000
    assert provider.config.temperature == 0.5
    assert provider.config.supports_images is True


def test_factory_logging(caplog):
    """Factory logs provider creation."""
    config = ModelConfig(
        provider=ProviderType.OPENAI_COMPATIBLE,
        name="Test Model",
        base_url="http://localhost:11434/v1",
        model="test",
    )

    with caplog.at_level("INFO"):
        create_provider(config)

    assert "Created OpenAI-compatible provider" in caplog.text
    assert "Test Model" in caplog.text
