"""AI provider implementations."""

import logging

from ai_chat.config.models import ModelConfig, ProviderType

from .base import (
    AuthenticationError,
    BaseProvider,
    ConnectionError,
    Message,
    ProviderError,
    RateLimitError,
    StreamChunk,
)
from .bedrock import BedrockProvider
from .openai_compatible import OpenAICompatibleProvider

logger = logging.getLogger(__name__)

__all__ = [
    "BaseProvider",
    "Message",
    "StreamChunk",
    "ProviderError",
    "AuthenticationError",
    "ConnectionError",
    "RateLimitError",
    "create_provider",
]


def create_provider(config: ModelConfig) -> BaseProvider:
    """
    Factory function to create appropriate provider based on config.

    Args:
        config: Model configuration

    Returns:
        Instantiated provider

    Raises:
        ValueError: If provider type is unknown
    """
    logger.debug(f"Creating provider for {config.name} (type: {config.provider})")

    if config.provider == ProviderType.BEDROCK:
        provider = BedrockProvider(config)
        logger.info(f"Created Bedrock provider: {config.name}")
        return provider

    elif config.provider == ProviderType.OPENAI_COMPATIBLE:
        provider = OpenAICompatibleProvider(config)
        logger.info(f"Created OpenAI-compatible provider: {config.name}")
        return provider

    else:
        raise ValueError(
            f"Unknown provider type: {config.provider}. "
            f"Supported types: {', '.join([t.value for t in ProviderType])}"
        )
