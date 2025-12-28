"""AI Chat source plugin implementation."""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QWidget

from ai_chat.config.loader import load_config
from ai_chat.contracts import (
    Source,
    SourceType,
    FormatHint,
    CapturePayload,
    Provenance,
    SourceContext,
)
from ai_chat.ui.chat_widget import ChatWidget

logger = logging.getLogger(__name__)


class AIChatSource:
    """AI Chat source plugin for capturing AI responses."""

    def __init__(self):
        """Initialize AI Chat source."""
        self._widget: Optional[ChatWidget] = None
        self._context: Optional[SourceContext] = None
        logger.info("AIChatSource initialized")

    @property
    def source_id(self) -> str:
        """Source identifier."""
        return "ai_chat"

    @property
    def display_name(self) -> str:
        """Display name."""
        return "AI Chat"

    @property
    def icon(self) -> Optional[str]:
        """Icon path."""
        # Return path to icon if available
        icon_path = Path(__file__).parent / "assets" / "chat_icon.png"
        if icon_path.exists():
            return str(icon_path)
        return None

    @property
    def capabilities(self) -> dict:
        """Source capabilities."""
        return {
            "supports_selection": True,
            "supports_full_capture": True,
            "supports_streaming": False,
            "supports_attachments": False,
        }

    def create_widget(self, context: SourceContext) -> QWidget:
        """
        Create chat widget in source mode.

        Args:
            context: Source context with callbacks

        Returns:
            ChatWidget configured for source mode
        """
        # Store context for later use
        self._context = context

        # Load configuration
        try:
            config = load_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            # Use context to get config or create minimal default
            config = load_config()  # Will use defaults

        # Create chat widget in source mode
        self._widget = ChatWidget(config, source_mode=True, source_context=context)

        logger.info("Created AI Chat widget in source mode")
        return self._widget

    def get_selection(self) -> Optional[CapturePayload]:
        """
        Get selected text from chat display.

        Returns:
            CapturePayload with selected text, or None if no selection
        """
        if not self._widget:
            logger.warning("Widget not created yet")
            return None

        # Get selected text from chat display
        selected_text = self._widget.chat_display.text_browser.textCursor().selectedText()

        if not selected_text:
            logger.debug("No text selected")
            return None

        # Create provenance
        provenance = Provenance(
            source_id=self.source_id,
            source_name=self.display_name,
            extra={
                "model": self._widget.chat_service.get_current_model_name(),
                "selection": True,
            }
        )

        # Create capture payload
        payload = CapturePayload(
            content=selected_text,
            source_type=SourceType.TEXT,
            format_hint=FormatHint.PLAIN_TEXT,
            title="AI Chat Selection",
            provenance=provenance,
        )

        logger.info(f"Captured selection: {len(selected_text)} characters")
        return payload

    def get_full_capture(self) -> Optional[CapturePayload]:
        """
        Get full content of last AI response.

        Returns:
            CapturePayload with last AI response, or None if no response
        """
        if not self._widget:
            logger.warning("Widget not created yet")
            return None

        # Get last assistant message
        last_message = self._widget.chat_display.get_last_assistant_message()

        if not last_message:
            logger.debug("No AI response available")
            return None

        # Create provenance
        provenance = Provenance(
            source_id=self.source_id,
            source_name=self.display_name,
            extra={
                "model": self._widget.chat_service.get_current_model_name(),
                "message_count": self._widget.chat_display.message_count,
            }
        )

        # Create capture payload
        payload = CapturePayload(
            content=last_message,
            source_type=SourceType.TEXT,
            format_hint=FormatHint.MARKDOWN,
            title="AI Chat Response",
            provenance=provenance,
        )

        logger.info(f"Captured full response: {len(last_message)} characters")
        return payload

    def shutdown(self) -> None:
        """Clean up resources."""
        logger.info("Shutting down AI Chat source")
        self._widget = None
        self._context = None
