"""Sidebar for conversation list and management."""

import logging
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ai_chat.services.storage import StorageService
from ai_chat.ui.styles import ThemeType

logger = logging.getLogger(__name__)


def get_sidebar_style(theme: ThemeType = "dark") -> str:
    """
    Get QSS stylesheet for conversation sidebar.

    Args:
        theme: Theme type ('dark' or 'light')

    Returns:
        QSS stylesheet string
    """
    if theme == "dark":
        return """
            QWidget#sidebar {
                background-color: #252526;
                border-right: 1px solid #3c3c3c;
            }
            QLabel {
                color: #d4d4d4;
                font-weight: bold;
                font-size: 14px;
            }
            QListWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px 8px;
                border-bottom: 1px solid #3c3c3c;
            }
            QListWidget::item:selected {
                background-color: #094771;
            }
            QListWidget::item:hover:!selected {
                background-color: #2a2d2e;
            }
            QPushButton {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0d5689;
            }
            QPushButton:disabled {
                background-color: #3c3c3c;
                color: #808080;
            }
            QPushButton#deleteBtn {
                background-color: #5a1d1d;
            }
            QPushButton#deleteBtn:hover {
                background-color: #7a2d2d;
            }
            QPushButton#deleteBtn:disabled {
                background-color: #3c3c3c;
                color: #808080;
            }
        """
    else:  # light theme
        return """
            QWidget#sidebar {
                background-color: #f3f3f3;
                border-right: 1px solid #d4d4d4;
            }
            QLabel {
                color: #1e1e1e;
                font-weight: bold;
                font-size: 14px;
            }
            QListWidget {
                background-color: #ffffff;
                color: #1e1e1e;
                border: 1px solid #d4d4d4;
                border-radius: 4px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px 8px;
                border-bottom: 1px solid #e8e8e8;
            }
            QListWidget::item:selected {
                background-color: #cce5ff;
            }
            QListWidget::item:hover:!selected {
                background-color: #e8e8e8;
            }
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #f0f0f0;
                color: #a0a0a0;
            }
            QPushButton#deleteBtn {
                background-color: #d32f2f;
            }
            QPushButton#deleteBtn:hover {
                background-color: #e53935;
            }
            QPushButton#deleteBtn:disabled {
                background-color: #f0f0f0;
                color: #a0a0a0;
            }
        """


class ConversationSidebar(QWidget):
    """Sidebar showing conversation list with new/load/delete actions."""

    # Signals
    new_conversation_requested = pyqtSignal()
    conversation_selected = pyqtSignal(str)  # conversation_id
    delete_requested = pyqtSignal(str)  # conversation_id

    def __init__(
        self,
        storage: StorageService,
        theme: ThemeType = "dark",
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize conversation sidebar.

        Args:
            storage: Storage service for persistence
            theme: Theme type ('dark' or 'light')
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.storage = storage
        self.theme = theme
        self._current_id: Optional[str] = None

        self.setObjectName("sidebar")
        self._create_ui()
        self._apply_style()
        self.refresh()

    def _create_ui(self) -> None:
        """Create UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header with New button
        header = QHBoxLayout()
        header.addWidget(QLabel("Conversations"))
        header.addStretch()

        self.new_btn = QPushButton("+ New")
        self.new_btn.setFixedWidth(70)
        self.new_btn.clicked.connect(self._on_new_clicked)
        header.addWidget(self.new_btn)

        layout.addLayout(header)

        # Conversation list
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

        # Delete button (bottom)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setObjectName("deleteBtn")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        layout.addWidget(self.delete_btn)

        # Sizing
        self.setMaximumWidth(280)
        self.setMinimumWidth(200)

    def _apply_style(self) -> None:
        """Apply theme-appropriate styling."""
        self.setStyleSheet(get_sidebar_style(self.theme))

    def set_theme(self, theme: ThemeType) -> None:
        """
        Update the theme.

        Args:
            theme: New theme type
        """
        self.theme = theme
        self._apply_style()

    def refresh(self) -> None:
        """Refresh conversation list from storage."""
        self.list_widget.clear()

        conversations = self.storage.list_conversations()

        for conv in conversations:
            item = QListWidgetItem()
            # Show title and message count
            msg_text = "message" if conv.message_count == 1 else "messages"
            item.setText(f"{conv.title}\n{conv.message_count} {msg_text}")
            item.setData(Qt.ItemDataRole.UserRole, conv.id)
            self.list_widget.addItem(item)

            # Select current conversation
            if conv.id == self._current_id:
                item.setSelected(True)
                self.list_widget.setCurrentItem(item)

        logger.debug(f"Refreshed conversation list: {len(conversations)} items")

    def set_current_conversation(self, conversation_id: Optional[str]) -> None:
        """
        Set the currently active conversation.

        Args:
            conversation_id: ID of active conversation, or None
        """
        self._current_id = conversation_id
        self.delete_btn.setEnabled(conversation_id is not None)

        # Update selection in list
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == conversation_id:
                item.setSelected(True)
                self.list_widget.setCurrentItem(item)
            elif item:
                item.setSelected(False)

    def _on_new_clicked(self) -> None:
        """Handle new conversation button."""
        logger.debug("New conversation requested")
        self.new_conversation_requested.emit()

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle conversation selection."""
        conversation_id = item.data(Qt.ItemDataRole.UserRole)
        if conversation_id and conversation_id != self._current_id:
            logger.debug(f"Conversation selected: {conversation_id}")
            self.conversation_selected.emit(conversation_id)

    def _on_delete_clicked(self) -> None:
        """Handle delete button."""
        if not self._current_id:
            return

        # Get current conversation title for confirmation
        current_item = self.list_widget.currentItem()
        title = current_item.text().split("\n")[0] if current_item else "this conversation"

        reply = QMessageBox.question(
            self,
            "Delete Conversation",
            f"Are you sure you want to delete '{title}'?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            logger.debug(f"Delete requested: {self._current_id}")
            self.delete_requested.emit(self._current_id)
