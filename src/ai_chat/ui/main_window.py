"""Main application window."""

import logging
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QMessageBox, QWidget

from ai_chat.config.models import Config
from ai_chat.services.storage import StorageService
from ai_chat.ui.chat_widget import ChatWidget
from ai_chat.ui.conversation_sidebar import ConversationSidebar

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(
        self,
        config: Config,
        storage: Optional[StorageService] = None,
    ):
        """
        Initialize main window.

        Args:
            config: Application configuration
            storage: Optional storage service for persistence
        """
        super().__init__()
        self.config = config
        self.storage = storage

        # Set window properties
        self.setWindowTitle(config.app.title)
        self.setMinimumSize(800, 600)
        self.resize(1100, 700)  # Slightly wider to accommodate sidebar

        # Determine theme
        theme = config.app.theme if config.app.theme != "system" else "dark"

        # Create central widget with horizontal layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add conversation sidebar if storage enabled
        if storage:
            self.sidebar = ConversationSidebar(storage, theme=theme)
            self.sidebar.new_conversation_requested.connect(self._on_new_conversation)
            self.sidebar.conversation_selected.connect(self._on_load_conversation)
            self.sidebar.delete_requested.connect(self._on_delete_conversation)
            layout.addWidget(self.sidebar)
        else:
            self.sidebar = None

        # Create chat widget (pass storage)
        self.chat_widget = ChatWidget(config, storage=storage)
        layout.addWidget(self.chat_widget, stretch=1)

        # Connect chat widget signals
        if self.sidebar:
            self.chat_widget.message_exchange_completed.connect(self._on_message_exchange_completed)

        # Create menu bar and actions
        self._create_menu_bar()

        # Start with new conversation if storage enabled
        if storage:
            self._on_new_conversation()

        logger.info(f"MainWindow initialized: {config.app.title}")

    def _create_menu_bar(self) -> None:
        """Create menu bar and actions."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # New conversation action (if storage enabled)
        if self.storage:
            new_action = QAction("&New Conversation", self)
            new_action.setShortcut(QKeySequence("Ctrl+N"))
            new_action.triggered.connect(self._on_new_conversation)
            file_menu.addAction(new_action)

            file_menu.addSeparator()

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

    def _on_new_conversation(self) -> None:
        """Handle new conversation request."""
        self.chat_widget.new_conversation()
        if self.sidebar:
            self.sidebar.refresh()
            self.sidebar.set_current_conversation(
                self.chat_widget.chat_service.conversation_id
            )
        logger.info("Started new conversation")

    def _on_message_exchange_completed(self) -> None:
        """Handle message exchange completion (refresh sidebar for title updates)."""
        if self.sidebar:
            self.sidebar.refresh()
            self.sidebar.set_current_conversation(
                self.chat_widget.chat_service.conversation_id
            )

    def _on_load_conversation(self, conversation_id: str) -> None:
        """
        Handle loading a conversation.

        Args:
            conversation_id: ID of conversation to load
        """
        if self.chat_widget.load_conversation(conversation_id):
            if self.sidebar:
                self.sidebar.set_current_conversation(conversation_id)
            logger.info(f"Loaded conversation: {conversation_id}")

    def _on_delete_conversation(self, conversation_id: str) -> None:
        """
        Handle deleting a conversation.

        Args:
            conversation_id: ID of conversation to delete
        """
        if self.storage:
            self.storage.delete_conversation(conversation_id)
            logger.info(f"Deleted conversation: {conversation_id}")

            # If deleted current conversation, start new one
            if self.chat_widget.chat_service.conversation_id == conversation_id:
                self._on_new_conversation()
            elif self.sidebar:
                self.sidebar.refresh()

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
            if self.sidebar:
                self.sidebar.refresh()
                self.sidebar.set_current_conversation(
                    self.chat_widget.chat_service.conversation_id
                )
            logger.info("User cleared conversation via menu")

    def _on_copy_last_response(self) -> None:
        """Handle copy last response action."""
        # Trigger the copy button in chat display
        self.chat_widget.chat_display._on_copy_last()
        logger.info("User triggered copy last response via shortcut")

    def _on_focus_input(self) -> None:
        """Handle focus input action."""
        self.chat_widget.input_widget.text_input.setFocus()
        logger.debug("Input widget focused via shortcut")

    def _on_about(self) -> None:
        """Handle about action."""
        persistence_info = ""
        if self.storage:
            persistence_info = "<li>Conversation persistence</li>"

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
            {persistence_info}
        </ul>
        <p><b>Keyboard Shortcuts:</b></p>
        <ul>
            <li>Ctrl+Enter: Send message</li>
            <li>Ctrl+Shift+C: Copy last response</li>
            <li>Ctrl+L: Focus input</li>
            <li>Ctrl+Shift+K: Clear conversation</li>
            {"<li>Ctrl+N: New conversation</li>" if self.storage else ""}
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
