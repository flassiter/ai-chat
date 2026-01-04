"""Base provider interface and data models."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Literal


@dataclass
class Message:
    """Represents a single message in the conversation."""

    role: Literal["user", "assistant", "system"]
    content: str
    images: list[bytes] = field(default_factory=list)
    documents: list[tuple[str, bytes]] = field(default_factory=list)  # (filename, data)


@dataclass
class StreamChunk:
    """Represents a chunk of streamed response."""

    content: str = ""
    reasoning: str = ""
    is_reasoning: bool = False
    done: bool = False


class BaseProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def stream_chat(
        self, messages: list[Message], max_tokens: int, temperature: float
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream chat completion responses.

        Args:
            messages: List of conversation messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 2.0)

        Yields:
            StreamChunk objects containing response content

        Raises:
            ConnectionError: If provider is unreachable
            AuthenticationError: If authentication fails
            ProviderError: For other provider-specific errors
        """
        pass

    @abstractmethod
    def supports_feature(self, feature: str) -> bool:
        """
        Check if provider/model supports a specific feature.

        Args:
            feature: Feature name (e.g., "images", "documents", "reasoning")

        Returns:
            True if feature is supported
        """
        pass


class ProviderError(Exception):
    """Base exception for provider errors."""

    pass


class AuthenticationError(ProviderError):
    """Authentication with provider failed."""

    pass


class ConnectionError(ProviderError):
    """Connection to provider failed."""

    pass


class RateLimitError(ProviderError):
    """Provider rate limit exceeded."""

    pass
