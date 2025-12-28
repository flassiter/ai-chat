"""Main chat widget combining all UI components."""

import asyncio
import logging
from typing import Optional

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from ai_chat.config.models import Config
from ai_chat.providers.base import ProviderError
from ai_chat.services import ChatService
from ai_chat.ui.chat_display import ChatDisplay
from ai_chat.ui.input_widget import InputWidget
from ai_chat.ui.model_selector import ModelSelector

logger = logging.getLogger(__name__)


class ChatWidget(QWidget):
    """Main chat widget with model selector, display, and input."""

    def __init__(
        self,
        config: Config,
        parent: QWidget | None = None,
        source_mode: bool = False,
        source_context: Optional[object] = None,
    ):
        """
        Initialize chat widget.

        Args:
            config: Application configuration
            parent: Parent widget
            source_mode: Whether running as source plugin
            source_context: Source context (if in source mode)
        """
        super().__init__(parent)
        self.config = config
        self.source_mode = source_mode
        self.source_context = source_context

        # Create chat service
        self.chat_service = ChatService(config)

        # Create UI
        self._create_ui()

        # Connect signals
        self._connect_signals()

        mode_str = "source mode" if source_mode else "standalone mode"
        logger.info(f"ChatWidget initialized in {mode_str}")

    def _create_ui(self) -> None:
        """Create UI components."""
        layout = QVBoxLayout(self)

        # Get theme from config
        theme = self.config.app.theme

        # Model selector at top
        self.model_selector = ModelSelector(self.config)
        layout.addWidget(self.model_selector)

        # Chat display (main area) with theme and source mode
        self.chat_display = ChatDisplay(
            theme=theme,
            source_mode=self.source_mode,
            source_context=self.source_context,
        )
        layout.addWidget(self.chat_display, stretch=1)

        # Input widget at bottom
        self.input_widget = InputWidget()
        layout.addWidget(self.input_widget)

        # Set margins
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        # Model selection changed
        self.model_selector.model_changed.connect(self._on_model_changed)

        # Message submitted
        self.input_widget.message_submitted.connect(self._on_message_submitted)

    def _on_model_changed(self, model_key: str) -> None:
        """
        Handle model selection change.

        Args:
            model_key: Selected model key
        """
        logger.info(f"Model changed to: {model_key}")
        self.chat_service.set_model(model_key)

    def _on_message_submitted(self, message: str, images: list, documents: list) -> None:
        """
        Handle message submission.

        Args:
            message: User message
            images: List of image data (bytes)
            documents: List of (filename, data) tuples
        """
        attachment_info = []
        if images:
            attachment_info.append(f"{len(images)} image(s)")
        if documents:
            attachment_info.append(f"{len(documents)} document(s)")
        attachment_str = f" with {', '.join(attachment_info)}" if attachment_info else ""

        logger.info(f"Message submitted{attachment_str}: {message[:50]}...")

        # Display user message immediately
        self.chat_display.append_user_message(message)

        # Disable input while processing
        self.input_widget.set_enabled(False)

        # Start streaming response (async)
        asyncio.create_task(self._stream_response(message, images, documents))

    async def _stream_response(self, user_message: str, images: list, documents: list) -> None:
        """
        Stream AI response asynchronously.

        Args:
            user_message: User's message
            images: List of image data (bytes)
            documents: List of (filename, data) tuples
        """
        try:
            # Start assistant message
            self.chat_display.append_assistant_message_start()

            # Stream response chunks with attachments
            async for chunk in self.chat_service.stream_response(user_message, images, documents):
                if chunk.content:
                    self.chat_display.append_assistant_chunk(chunk.content)

                if chunk.reasoning:
                    self.chat_display.append_reasoning_chunk(chunk.reasoning)

                if chunk.done:
                    break

            # End assistant message
            self.chat_display.append_assistant_message_end()

            logger.info("Response streaming completed")

        except ValueError as e:
            # Capability error (model doesn't support attachments)
            logger.error(f"Capability error: {e}")
            self.chat_display.append_error(str(e))

        except ProviderError as e:
            logger.error(f"Provider error: {e}")
            self.chat_display.append_error(str(e))

        except Exception as e:
            logger.error(f"Unexpected error during streaming: {e}", exc_info=True)
            self.chat_display.append_error(f"Unexpected error: {e}")

        finally:
            # Re-enable input
            self.input_widget.set_enabled(True)
            self.input_widget.focus_input()

    def clear_conversation(self) -> None:
        """Clear the conversation."""
        self.chat_service.clear_history()
        self.chat_display.clear_display()
        logger.info("Conversation cleared")
