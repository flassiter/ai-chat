"""Chat service for managing conversations and routing to providers."""

import logging
from typing import AsyncIterator, Optional

from ai_chat.config.models import Config, ModelConfig
from ai_chat.providers import BaseProvider, Message, StreamChunk, create_provider

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat conversations."""

    def __init__(self, config: Config):
        """
        Initialize chat service with configuration.

        Args:
            config: Application configuration
        """
        self.config = config
        self.messages: list[Message] = []
        self.current_model_key: str = config.app.default_model

        logger.info(
            f"ChatService initialized with default model: {self.current_model_key}"
        )

    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the conversation history.

        Args:
            role: "user" or "assistant"
            content: Message content
        """
        message = Message(role=role, content=content)
        self.messages.append(message)

        logger.info(f"Added {role} message to history (total: {len(self.messages)})")
        logger.debug(f"Message content: {content[:100]}...")

    def clear_history(self) -> None:
        """Clear all conversation history."""
        message_count = len(self.messages)
        self.messages.clear()
        logger.info(f"Cleared conversation history ({message_count} messages)")

    def set_model(self, model_key: str) -> None:
        """
        Set the active model.

        Args:
            model_key: Key of model in config

        Raises:
            ValueError: If model_key not found
        """
        if model_key not in self.config.models:
            available = ", ".join(self.config.models.keys())
            raise ValueError(
                f"Model '{model_key}' not found. Available: {available}"
            )

        self.current_model_key = model_key
        logger.info(f"Switched to model: {model_key}")

    def get_current_model_config(self) -> ModelConfig:
        """
        Get configuration for currently selected model.

        Returns:
            ModelConfig for current model
        """
        return self.config.models[self.current_model_key]

    def get_current_model_name(self) -> str:
        """
        Get display name of currently selected model.

        Returns:
            Model display name
        """
        return self.config.models[self.current_model_key].name

    def _create_provider(self, model_config: ModelConfig) -> BaseProvider:
        """
        Create provider instance for model config using factory.

        Args:
            model_config: Model configuration

        Returns:
            Provider instance

        Raises:
            ValueError: If provider type not supported
        """
        return create_provider(model_config)

    async def stream_response(
        self, user_message: str
    ) -> AsyncIterator[StreamChunk]:
        """
        Send user message and stream AI response.

        Args:
            user_message: User's message

        Yields:
            StreamChunk objects with response content
        """
        # Add user message to history
        self.add_message("user", user_message)

        # Get current model config
        model_config = self.get_current_model_config()

        logger.info(
            f"Streaming response from {model_config.name} "
            f"(conversation length: {len(self.messages)})"
        )

        # Create provider
        provider = self._create_provider(model_config)

        # Stream response
        assistant_message = ""
        try:
            async for chunk in provider.stream_chat(
                self.messages,
                max_tokens=model_config.max_tokens,
                temperature=model_config.temperature,
            ):
                # Accumulate assistant message
                if chunk.content:
                    assistant_message += chunk.content

                yield chunk

            # Add complete assistant message to history
            if assistant_message:
                self.add_message("assistant", assistant_message)

        except Exception as e:
            logger.error(f"Error during streaming: {e}", exc_info=True)
            # Don't add failed response to history
            raise

    @property
    def message_count(self) -> int:
        """Get number of messages in conversation."""
        return len(self.messages)

    def get_history(self) -> list[Message]:
        """
        Get conversation history.

        Returns:
            List of Message objects
        """
        return self.messages.copy()
