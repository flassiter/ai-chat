"""Main application window."""

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QMainWindow, QMessageBox

from ai_chat.config.models import Config
from ai_chat.ui.chat_widget import ChatWidget

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, config: Config):
        """
        Initialize main window.

        Args:
            config: Application configuration
        """
        super().__init__()
        self.config = config

        # Set window properties
        self.setWindowTitle(config.app.title)
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)

        # Create central widget
        self.chat_widget = ChatWidget(config)
        self.setCentralWidget(self.chat_widget)

        # Create menu bar and actions
        self._create_menu_bar()

        logger.info(f"MainWindow initialized: {config.app.title}")

    def _create_menu_bar(self) -> None:
        """Create menu bar and actions."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # Clear conversation action
        clear_action = QAction("&Clear Conversation", self)
        clear_action.setShortcut(QKeySequence("Ctrl+Shift+K"))
        clear_action.triggered.connect(self._on_clear_conversation)
        file_menu.addAction(clear_action)

        file_menu.addSeparator()

        # Quit action
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        # Copy last response action
        copy_action = QAction("Copy &Last Response", self)
        copy_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        copy_action.triggered.connect(self._on_copy_last_response)
        edit_menu.addAction(copy_action)

        # Focus input action
        focus_action = QAction("&Focus Input", self)
        focus_action.setShortcut(QKeySequence("Ctrl+L"))
        focus_action.triggered.connect(self._on_focus_input)
        edit_menu.addAction(focus_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _on_clear_conversation(self) -> None:
        """Handle clear conversation action."""
        reply = QMessageBox.question(
            self,
            "Clear Conversation",
            "Are you sure you want to clear the conversation history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.chat_widget.clear_conversation()
            logger.info("User cleared conversation via menu")

    def _on_copy_last_response(self) -> None:
        """Handle copy last response action."""
        # Trigger the copy button in chat display
        self.chat_widget.chat_display._on_copy_last()
        logger.info("User triggered copy last response via shortcut")

    def _on_focus_input(self) -> None:
        """Handle focus input action."""
        self.chat_widget.input_widget.text_edit.setFocus()
        logger.debug("Input widget focused via shortcut")

    def _on_about(self) -> None:
        """Handle about action."""
        about_text = f"""
        <h2>{self.config.app.title}</h2>
        <p>Version 1.0.0</p>
        <p>Chat interface for local and AWS Bedrock AI models.</p>
        <p><b>Features:</b></p>
        <ul>
            <li>Multi-provider support (Ollama, LM Studio, AWS Bedrock)</li>
            <li>Streaming responses</li>
            <li>Markdown rendering with syntax highlighting</li>
            <li>Copy functionality</li>
            <li>Configurable models via TOML</li>
        </ul>
        <p><b>Keyboard Shortcuts:</b></p>
        <ul>
            <li>Ctrl+Enter: Send message</li>
            <li>Ctrl+Shift+C: Copy last response</li>
            <li>Ctrl+L: Focus input</li>
            <li>Ctrl+Shift+K: Clear conversation</li>
            <li>Ctrl+Q: Quit</li>
        </ul>
        """

        QMessageBox.about(self, "About", about_text)

    def closeEvent(self, event) -> None:
        """
        Handle window close event.

        Args:
            event: Close event
        """
        logger.info("Main window closing")
        event.accept()
