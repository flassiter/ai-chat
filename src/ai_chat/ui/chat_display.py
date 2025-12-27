"""Enhanced chat display widget with markdown rendering."""

import logging
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QTextBrowser,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
)

from ai_chat.utils.clipboard import copy_to_clipboard
from ai_chat.utils.markdown import render_markdown, get_pygments_css
from ai_chat.ui.styles import (
    get_chat_display_style,
    get_message_html,
    get_error_html,
    get_code_block_css,
    get_copy_button_style,
    ThemeType,
)

logger = logging.getLogger(__name__)


class ChatDisplay(QWidget):
    """Enhanced chat display with markdown rendering and copy functionality."""

    # Signal emitted when copy button is clicked
    copy_requested = pyqtSignal(str)

    def __init__(self, theme: ThemeType = "dark", parent: Optional[QWidget] = None):
        """
        Initialize chat display.

        Args:
            theme: UI theme ('dark' or 'light')
            parent: Parent widget
        """
        super().__init__(parent)

        self.theme = theme
        self._messages: list[tuple[str, str, str]] = []  # (role, content_md, content_html)
        self._current_assistant_message = ""

        # Create text browser for HTML rendering
        self.text_browser = QTextBrowser()
        self.text_browser.setReadOnly(True)
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setStyleSheet(get_chat_display_style(theme))

        # Set custom CSS for code blocks and Pygments
        css = get_code_block_css(theme) + "\n" + get_pygments_css("monokai" if theme == "dark" else "default")
        self.text_browser.document().setDefaultStyleSheet(css)

        # Create copy button
        self.copy_button = QPushButton("📋 Copy Last Response")
        self.copy_button.setStyleSheet(get_copy_button_style(theme))
        self.copy_button.clicked.connect(self._on_copy_last)
        self.copy_button.setEnabled(False)

        # Copy feedback label
        self.copy_feedback = QLabel("")
        self.copy_feedback.setStyleSheet("color: #6c9e4e; font-size: 12px;")
        self.copy_feedback.hide()

        # Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Button bar
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.copy_button)
        button_layout.addWidget(self.copy_feedback)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.text_browser)

        logger.info(f"ChatDisplay initialized with {theme} theme")

    def append_user_message(self, content: str) -> None:
        """
        Append a user message to the display.

        Args:
            content: Message content (plain text)
        """
        # User messages are plain text, no markdown rendering needed
        html_content = content.replace("\n", "<br>").replace(" ", "&nbsp;")
        message_html = get_message_html(html_content, "user", self.theme)

        self._messages.append(("user", content, message_html))
        self._update_display()

        logger.debug(f"Appended user message: {content[:50]}...")

    def append_assistant_message_start(self) -> None:
        """Start a new assistant message."""
        self._current_assistant_message = ""
        logger.debug("Started assistant message")

    def append_assistant_chunk(self, content: str) -> None:
        """
        Append content to the current assistant message.

        Args:
            content: Content chunk to append (markdown)
        """
        self._current_assistant_message += content

        # Render markdown
        html_content = render_markdown(self._current_assistant_message, "monokai" if self.theme == "dark" else "default")
        message_html = get_message_html(html_content, "assistant", self.theme)

        # Update display (replace last message if it exists and is assistant)
        if self._messages and self._messages[-1][0] == "assistant":
            self._messages[-1] = ("assistant", self._current_assistant_message, message_html)
        else:
            self._messages.append(("assistant", self._current_assistant_message, message_html))

        self._update_display()

    def append_assistant_message_end(self) -> None:
        """End the current assistant message."""
        # Final render
        if self._current_assistant_message:
            html_content = render_markdown(self._current_assistant_message, "monokai" if self.theme == "dark" else "default")
            message_html = get_message_html(html_content, "assistant", self.theme)

            if self._messages and self._messages[-1][0] == "assistant":
                self._messages[-1] = ("assistant", self._current_assistant_message, message_html)
            else:
                self._messages.append(("assistant", self._current_assistant_message, message_html))

            self._update_display()

        # Enable copy button
        self.copy_button.setEnabled(True)

        self._current_assistant_message = ""
        logger.debug("Ended assistant message")

    def append_error(self, error_message: str) -> None:
        """
        Append an error message to the display.

        Args:
            error_message: Error message to display
        """
        error_html = get_error_html(error_message, self.theme)
        # Append directly as HTML
        current_html = self.text_browser.toHtml()
        self.text_browser.setHtml(current_html + error_html)
        self._scroll_to_bottom()

        logger.warning(f"Displayed error: {error_message}")

    def clear_display(self) -> None:
        """Clear all content from display."""
        self._messages.clear()
        self._current_assistant_message = ""
        self.text_browser.clear()
        self.copy_button.setEnabled(False)
        self.copy_feedback.hide()
        logger.info("Chat display cleared")

    def get_last_assistant_message(self) -> Optional[str]:
        """
        Get the last assistant message content (markdown).

        Returns:
            Last assistant message markdown, or None if no messages
        """
        for role, content_md, _ in reversed(self._messages):
            if role == "assistant":
                return content_md
        return None

    def _update_display(self) -> None:
        """Update the display with all messages."""
        # Combine all message HTML
        html = "".join(msg[2] for msg in self._messages)
        self.text_browser.setHtml(html)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        """Scroll to bottom of display."""
        scrollbar = self.text_browser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_copy_last(self) -> None:
        """Handle copy last response button click."""
        last_message = self.get_last_assistant_message()
        if last_message:
            if copy_to_clipboard(last_message):
                self.copy_feedback.setText("✓ Copied!")
                self.copy_feedback.show()
                logger.info("Copied last response to clipboard")

                # Hide feedback after 2 seconds
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(2000, self.copy_feedback.hide)
            else:
                self.copy_feedback.setText("✗ Failed to copy")
                self.copy_feedback.setStyleSheet("color: #f48771; font-size: 12px;")
                self.copy_feedback.show()
                logger.error("Failed to copy last response")

    @property
    def message_count(self) -> int:
        """
        Get message count.

        Returns:
            Number of messages (user + assistant)
        """
        return len(self._messages)
