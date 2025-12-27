"""Chat input widget with send button."""

import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QKeyEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class InputWidget(QWidget):
    """Input widget with multi-line text and send button."""

    message_submitted = pyqtSignal(str)  # Emits message content

    def __init__(self, parent: QWidget | None = None):
        """
        Initialize input widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Create UI components
        self._create_ui()

        logger.info("InputWidget initialized")

    def _create_ui(self) -> None:
        """Create UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Text input
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Type your message here...")
        self.text_input.setMaximumHeight(120)
        self.text_input.setMinimumHeight(60)

        # Set font
        font = QFont("Monospace", 10)
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        self.text_input.setFont(font)

        # Styling
        self.text_input.setStyleSheet(
            """
            QTextEdit {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 8px;
            }
            QTextEdit:focus {
                border: 1px solid #007acc;
            }
            """
        )

        # Install event filter to handle Ctrl+Enter
        self.text_input.installEventFilter(self)

        # Button row
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.setMinimumWidth(100)
        self.send_button.setStyleSheet(
            """
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0d5a8f;
            }
            QPushButton:disabled {
                background-color: #3e3e3e;
                color: #7f7f7f;
            }
            """
        )
        self.send_button.clicked.connect(self._on_send_clicked)

        button_layout.addWidget(self.send_button)

        # Add to layout
        layout.addWidget(self.text_input)
        layout.addLayout(button_layout)

    def eventFilter(self, obj, event) -> bool:
        """
        Event filter to handle Ctrl+Enter.

        Args:
            obj: Object that generated event
            event: Event

        Returns:
            True if event was handled
        """
        if obj == self.text_input and event.type() == event.Type.KeyPress:
            key_event = event
            # Ctrl+Enter or Cmd+Enter sends message
            if (
                key_event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
                and key_event.modifiers() & Qt.KeyboardModifier.ControlModifier
            ):
                self._on_send_clicked()
                return True

        return super().eventFilter(obj, event)

    def _on_send_clicked(self) -> None:
        """Handle send button click."""
        text = self.text_input.toPlainText().strip()

        if not text:
            logger.debug("Send clicked but input is empty")
            return

        logger.info(f"Message submitted: {text[:50]}...")

        # Emit signal
        self.message_submitted.emit(text)

        # Clear input
        self.text_input.clear()

    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable input.

        Args:
            enabled: Whether to enable input
        """
        self.text_input.setEnabled(enabled)
        self.send_button.setEnabled(enabled)

    def focus_input(self) -> None:
        """Focus the text input."""
        self.text_input.setFocus()

    def get_text(self) -> str:
        """
        Get current input text.

        Returns:
            Input text
        """
        return self.text_input.toPlainText()

    def clear_input(self) -> None:
        """Clear the input field."""
        self.text_input.clear()
