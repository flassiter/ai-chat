"""Source protocol definition."""

from typing import Protocol, Optional
from PyQt6.QtWidgets import QWidget

from .capture import CapturePayload
from .context import SourceContext


class Source(Protocol):
    """Protocol for source plugins that provide content to capture."""

    @property
    def source_id(self) -> str:
        """
        Unique identifier for this source.

        Returns:
            Source ID (e.g., "ai_chat")
        """
        ...

    @property
    def display_name(self) -> str:
        """
        Human-readable name for this source.

        Returns:
            Display name (e.g., "AI Chat")
        """
        ...

    @property
    def icon(self) -> Optional[str]:
        """
        Path to icon file for this source.

        Returns:
            Icon path or None
        """
        ...

    @property
    def capabilities(self) -> dict:
        """
        Source capabilities.

        Returns:
            Dict with capability flags (e.g., {"supports_selection": True})
        """
        ...

    def create_widget(self, context: SourceContext) -> QWidget:
        """
        Create the source widget.

        Args:
            context: Source context with callbacks

        Returns:
            QWidget instance for the source
        """
        ...

    def get_selection(self) -> Optional[CapturePayload]:
        """
        Get currently selected content.

        Returns:
            CapturePayload if selection exists, None otherwise
        """
        ...

    def get_full_capture(self) -> Optional[CapturePayload]:
        """
        Get full content capture.

        Returns:
            CapturePayload with full content, or None if not available
        """
        ...

    def shutdown(self) -> None:
        """Clean up resources when source is being removed."""
        ...
