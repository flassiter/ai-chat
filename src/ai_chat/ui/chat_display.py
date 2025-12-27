"""Chat display widget for showing conversation."""

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import QTextEdit, QWidget

logger = logging.getLogger(__name__)


class ChatDisplay(QTextEdit):
    """Text display for chat conversation."""

    def __init__(self, parent: QWidget | None = None):
        """
        Initialize chat display.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Make read-only
        self.setReadOnly(True)

        # Set font
        font = QFont("Monospace", 10)
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        self.setFont(font)

        # Styling
        self.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 10px;
            }
            """
        )

        logger.info("ChatDisplay initialized")

    def append_user_message(self, content: str) -> None:
        """
        Append a user message to the display.

        Args:
            content: Message content
        """
        self.append("\n")
        self.append("=" * 80)
        self.append("YOU:")
        self.append(content)
        self.append("=" * 80)
        self.append("\n")

        # Scroll to bottom
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

        logger.debug(f"Appended user message: {content[:50]}...")

    def append_assistant_message_start(self) -> None:
        """Start a new assistant message."""
        self.append("ASSISTANT:")
        self._assistant_start_pos = self.textCursor().position()

        logger.debug("Started assistant message")

    def append_assistant_chunk(self, content: str) -> None:
        """
        Append content to the current assistant message.

        Args:
            content: Content chunk to append
        """
        # Move cursor to end
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.setTextCursor(cursor)

        # Insert text
        self.insertPlainText(content)

        # Scroll to bottom
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def append_assistant_message_end(self) -> None:
        """End the current assistant message."""
        self.append("\n")
        logger.debug("Ended assistant message")

    def append_error(self, error_message: str) -> None:
        """
        Append an error message to the display.

        Args:
            error_message: Error message to display
        """
        self.append("\n")
        self.append("!" * 80)
        self.append(f"ERROR: {error_message}")
        self.append("!" * 80)
        self.append("\n")

        # Scroll to bottom
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

        logger.warning(f"Displayed error: {error_message}")

    def clear_display(self) -> None:
        """Clear all content from display."""
        self.clear()
        logger.info("Chat display cleared")

    @property
    def message_count(self) -> int:
        """
        Get approximate message count.

        Returns:
            Number of messages (user + assistant)
        """
        # Simple approximation based on separator lines
        text = self.toPlainText()
        return text.count("YOU:") + text.count("ASSISTANT:")
