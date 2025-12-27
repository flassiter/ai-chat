"""Chat input widget with send button and attachment support."""

import io
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QByteArray, pyqtSignal
from PyQt6.QtGui import QFont, QKeyEvent, QPixmap, QImage
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ai_chat.services.attachments import (
    Attachment,
    create_attachment_from_file,
    create_attachment_from_bytes,
    UnsupportedFormatError,
    FileSizeError,
    SUPPORTED_IMAGE_FORMATS,
    SUPPORTED_DOCUMENT_FORMATS,
)

logger = logging.getLogger(__name__)


class AttachmentPreview(QWidget):
    """Widget to preview a single attachment with remove button."""

    remove_requested = pyqtSignal(object)  # Emits the attachment object

    def __init__(self, attachment: Attachment, parent: Optional[QWidget] = None):
        """Initialize attachment preview."""
        super().__init__(parent)
        self.attachment = attachment

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Preview area
        if attachment.attachment_type == "image":
            # Show image thumbnail
            pixmap = QPixmap()
            pixmap.loadFromData(attachment.data)
            if not pixmap.isNull():
                # Scale to thumbnail
                pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                image_label = QLabel()
                image_label.setPixmap(pixmap)
                layout.addWidget(image_label)
        else:
            # Show document icon
            doc_label = QLabel("📄")
            doc_label.setStyleSheet("font-size: 32px;")
            layout.addWidget(doc_label)

        # Filename label
        filename_label = QLabel(attachment.filename)
        filename_label.setWordWrap(True)
        filename_label.setMaximumWidth(80)
        filename_label.setStyleSheet("font-size: 10px;")
        layout.addWidget(filename_label)

        # Remove button
        remove_btn = QPushButton("×")
        remove_btn.setMaximumWidth(80)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #5a1d1d;
                color: white;
                border: none;
                border-radius: 2px;
                padding: 2px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7a2d2d;
            }
        """)
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.attachment))
        layout.addWidget(remove_btn)

        # Container styling
        self.setStyleSheet("""
            AttachmentPreview {
                background-color: #2d2d2d;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
            }
        """)
        self.setMaximumWidth(90)


class InputWidget(QWidget):
    """Input widget with multi-line text, attachments, and send button."""

    message_submitted = pyqtSignal(str, list, list)  # Emits (text, images, documents)

    def __init__(self, parent: QWidget | None = None):
        """
        Initialize input widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Track attachments
        self.attachments: list[Attachment] = []

        # Create UI components
        self._create_ui()

        logger.info("InputWidget initialized with attachment support")

    def _create_ui(self) -> None:
        """Create UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Attachment preview area (initially hidden)
        self.attachment_container = QWidget()
        self.attachment_layout = QHBoxLayout(self.attachment_container)
        self.attachment_layout.setContentsMargins(0, 0, 0, 8)
        self.attachment_container.hide()

        layout.addWidget(self.attachment_container)

        # Text input
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Type your message here... (Ctrl+V to paste images)")
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

        # Install event filter to handle Ctrl+Enter and paste
        self.text_input.installEventFilter(self)

        # Button row
        button_layout = QHBoxLayout()

        # Attach button
        self.attach_button = QPushButton("📎 Attach")
        self.attach_button.setToolTip("Attach image or document")
        self.attach_button.setStyleSheet(
            """
            QPushButton {
                background-color: #3e3e3e;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #4e4e4e;
            }
            QPushButton:pressed {
                background-color: #2e2e2e;
            }
            """
        )
        self.attach_button.clicked.connect(self._on_attach_clicked)
        button_layout.addWidget(self.attach_button)

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
        Event filter to handle Ctrl+Enter and paste.

        Args:
            obj: Object that generated event
            event: Event

        Returns:
            True if event was handled
        """
        if obj == self.text_input:
            if event.type() == event.Type.KeyPress:
                key_event = event
                # Ctrl+Enter or Cmd+Enter sends message
                if (
                    key_event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
                    and key_event.modifiers() & Qt.KeyboardModifier.ControlModifier
                ):
                    self._on_send_clicked()
                    return True

                # Ctrl+V for paste (check for images)
                if (
                    key_event.key() == Qt.Key.Key_V
                    and key_event.modifiers() & Qt.KeyboardModifier.ControlModifier
                ):
                    self._handle_paste()
                    return True

        return super().eventFilter(obj, event)

    def _handle_paste(self) -> None:
        """Handle clipboard paste (check for images)."""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()

        # Check if clipboard contains an image
        if mime_data.hasImage():
            image = clipboard.image()
            if not image.isNull():
                # Convert QImage to bytes
                byte_array = QByteArray()
                buffer = io.BytesIO()
                buffer_qt = QByteArray()

                # Save as PNG to buffer
                image.save(buffer_qt, "PNG")
                image_bytes = bytes(buffer_qt)

                # Create attachment from bytes
                try:
                    attachment = create_attachment_from_bytes(
                        image_bytes,
                        "pasted_image.png",
                        "image/png",
                        "image"
                    )
                    self.add_attachment(attachment)
                    logger.info("Added pasted image attachment")
                except Exception as e:
                    logger.error(f"Failed to add pasted image: {e}")

            # Don't paste the image into text
            return

        # Default paste behavior for text
        self.text_input.paste()

    def _on_attach_clicked(self) -> None:
        """Handle attach button click."""
        # Create file dialog
        supported = SUPPORTED_IMAGE_FORMATS | SUPPORTED_DOCUMENT_FORMATS
        extensions = " ".join(f"*{ext}" for ext in sorted(supported))
        filter_str = f"Supported Files ({extensions});;All Files (*)"

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Attach",
            "",
            filter_str
        )

        if file_path:
            try:
                attachment = create_attachment_from_file(Path(file_path))
                self.add_attachment(attachment)
                logger.info(f"Added file attachment: {attachment.filename}")
            except UnsupportedFormatError as e:
                logger.error(f"Unsupported format: {e}")
                # TODO: Show error message to user
            except FileSizeError as e:
                logger.error(f"File too large: {e}")
                # TODO: Show error message to user
            except Exception as e:
                logger.error(f"Failed to attach file: {e}", exc_info=True)
                # TODO: Show error message to user

    def add_attachment(self, attachment: Attachment) -> None:
        """
        Add an attachment and show preview.

        Args:
            attachment: Attachment to add
        """
        self.attachments.append(attachment)

        # Create preview widget
        preview = AttachmentPreview(attachment)
        preview.remove_requested.connect(self.remove_attachment)
        self.attachment_layout.addWidget(preview)

        # Show attachment container
        self.attachment_container.show()

        logger.debug(f"Added attachment preview: {attachment.filename}")

    def remove_attachment(self, attachment: Attachment) -> None:
        """
        Remove an attachment.

        Args:
            attachment: Attachment to remove
        """
        if attachment in self.attachments:
            self.attachments.remove(attachment)
            logger.debug(f"Removed attachment: {attachment.filename}")

            # Remove preview widget
            for i in range(self.attachment_layout.count()):
                widget = self.attachment_layout.itemAt(i).widget()
                if isinstance(widget, AttachmentPreview) and widget.attachment == attachment:
                    widget.deleteLater()
                    break

            # Hide container if no attachments
            if not self.attachments:
                self.attachment_container.hide()

    def _on_send_clicked(self) -> None:
        """Handle send button click."""
        text = self.text_input.toPlainText().strip()

        if not text and not self.attachments:
            logger.debug("Send clicked but input is empty and no attachments")
            return

        logger.info(f"Message submitted: {text[:50]}... with {len(self.attachments)} attachment(s)")

        # Separate images and documents
        images = []
        documents = []

        for attachment in self.attachments:
            if attachment.attachment_type == "image":
                images.append(attachment.data)
            else:
                documents.append((attachment.filename, attachment.data))

        # Emit signal with attachments
        self.message_submitted.emit(text, images, documents)

        # Clear input and attachments
        self.text_input.clear()
        self.clear_attachments()

    def clear_attachments(self) -> None:
        """Clear all attachments."""
        # Remove all preview widgets
        while self.attachment_layout.count():
            item = self.attachment_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.attachments.clear()
        self.attachment_container.hide()
        logger.debug("Cleared all attachments")

    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable input.

        Args:
            enabled: Whether to enable input
        """
        self.text_input.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
        self.attach_button.setEnabled(enabled)

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
        """Clear the input field and attachments."""
        self.text_input.clear()
        self.clear_attachments()
