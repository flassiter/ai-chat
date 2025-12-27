"""OpenAI-compatible provider for local models (Ollama, LM Studio, llama.cpp)."""

import json
import logging
from typing import AsyncIterator

import httpx

from ai_chat.config.models import ModelConfig
from ai_chat.providers.base import (
    AuthenticationError,
    BaseProvider,
    ConnectionError,
    Message,
    ProviderError,
    RateLimitError,
    StreamChunk,
)
from ai_chat.utils.reasoning import extract_reasoning_tags, has_reasoning_tags

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(BaseProvider):
    """Provider for OpenAI-compatible API endpoints."""

    def __init__(self, config: ModelConfig):
        """
        Initialize provider with model configuration.

        Args:
            config: ModelConfig with provider=openai_compatible
        """
        if not config.base_url:
            raise ValueError("OpenAI-compatible provider requires base_url")
        if not config.model:
            raise ValueError("OpenAI-compatible provider requires model")

        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.model = config.model
        self.api_key = config.api_key or "not-needed"

        logger.info(
            f"Initialized OpenAI-compatible provider: {config.name} "
            f"(base_url={self.base_url}, model={self.model})"
        )

    async def stream_chat(
        self, messages: list[Message], max_tokens: int, temperature: float
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream chat completion from OpenAI-compatible endpoint.

        Args:
            messages: Conversation history
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Yields:
            StreamChunk objects with response content

        Raises:
            ConnectionError: If unable to connect to server
            AuthenticationError: If API key is invalid
            RateLimitError: If rate limited
            ProviderError: For other errors
        """
        endpoint = f"{self.base_url}/chat/completions"

        # Convert messages to OpenAI format
        openai_messages = self._convert_messages(messages)

        payload = {
            "model": self.model,
            "messages": openai_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        logger.info(
            f"Starting chat stream: model={self.model}, "
            f"messages={len(messages)}, max_tokens={max_tokens}"
        )
        logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "POST",
                    endpoint,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                ) as response:
                    # Check for errors
                    if response.status_code == 401:
                        logger.error("Authentication failed")
                        raise AuthenticationError(
                            f"Authentication failed for {self.config.name}"
                        )
                    elif response.status_code == 429:
                        logger.warning("Rate limit exceeded")
                        raise RateLimitError(
                            f"Rate limit exceeded for {self.config.name}"
                        )
                    elif response.status_code >= 400:
                        error_text = await response.aread()
                        logger.error(
                            f"HTTP {response.status_code}: {error_text.decode()}"
                        )
                        raise ProviderError(
                            f"Provider error: HTTP {response.status_code}"
                        )

                    logger.debug("Stream started successfully")

                    # Parse SSE stream
                    async for chunk in self._parse_sse_stream(response):
                        yield chunk

                    logger.info("Stream completed successfully")

        except httpx.ConnectError as e:
            logger.error(f"Connection failed: {e}")
            raise ConnectionError(
                f"Cannot connect to {self.config.name} at {self.base_url}. "
                f"Is the server running?"
            )
        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {e}")
            raise ConnectionError(f"Request to {self.config.name} timed out")
        except (AuthenticationError, RateLimitError, ProviderError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise ProviderError(f"Unexpected error: {e}")

    async def _parse_sse_stream(
        self, response: httpx.Response
    ) -> AsyncIterator[StreamChunk]:
        """
        Parse Server-Sent Events stream.

        Args:
            response: httpx streaming response

        Yields:
            StreamChunk objects
        """
        async for line in response.aiter_lines():
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith(":"):
                continue

            # Parse SSE data line
            if line.startswith("data: "):
                data = line[6:].strip()

                # Check for stream end marker
                if data == "[DONE]":
                    logger.debug("Received [DONE] marker")
                    yield StreamChunk(done=True)
                    return

                try:
                    chunk_data = json.loads(data)
                    logger.debug(f"Received chunk: {chunk_data}")

                    # Extract content from choices
                    choices = chunk_data.get("choices", [])
                    if choices:
                        choice = choices[0]
                        delta = choice.get("delta", {})
                        content = delta.get("content", "")

                        if content:
                            yield StreamChunk(content=content)

                        # Check for finish reason
                        if choice.get("finish_reason"):
                            logger.debug(
                                f"Stream finished: {choice.get('finish_reason')}"
                            )
                            yield StreamChunk(done=True)

                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse SSE data: {data}, error: {e}")
                    continue

    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        """
        Convert Message objects to OpenAI API format.

        Args:
            messages: List of Message objects

        Returns:
            List of dicts in OpenAI format
        """
        openai_messages = []

        for msg in messages:
            # Basic text message
            message_dict = {"role": msg.role, "content": msg.content}

            # TODO: Handle images and documents in Phase 6
            # For now, just include text content

            openai_messages.append(message_dict)

        return openai_messages

    def supports_feature(self, feature: str) -> bool:
        """
        Check if this provider/model supports a feature.

        Args:
            feature: Feature name ("images", "documents", "reasoning")

        Returns:
            True if supported
        """
        if feature == "images":
            return self.config.supports_images
        elif feature == "documents":
            return self.config.supports_documents
        elif feature == "reasoning":
            return self.config.supports_reasoning
        else:
            return False
