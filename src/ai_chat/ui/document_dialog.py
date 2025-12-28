"""Dialog for previewing and saving generated documents."""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QTextBrowser,
    QFileDialog,
    QMessageBox,
    QWidget,
)

from ai_chat.services.document import GeneratedDocument, save_document
from ai_chat.utils.clipboard import copy_to_clipboard
from ai_chat.utils.markdown import render_markdown, get_pygments_css
from ai_chat.ui.styles import ThemeType, get_code_block_css

logger = logging.getLogger(__name__)


class DocumentDialog(QDialog):
    """Dialog for previewing and saving generated documents."""

    def __init__(
        self,
        document: GeneratedDocument,
        theme: ThemeType = "dark",
        parent: Optional[QWidget] = None,
        source_mode: bool = False,
        source_context: Optional[object] = None,
    ):
        """
        Initialize document dialog.

        Args:
            document: Generated document to preview
            theme: UI theme
            parent: Parent widget
            source_mode: Whether running in source plugin mode
            source_context: Source context (if in source mode)
        """
        super().__init__(parent)
        self.document = document
        self.theme = theme
        self.source_mode = source_mode
        self.source_context = source_context

        self.setWindowTitle("Generated Document")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        self._create_ui()

        mode_str = " (Source Mode)" if source_mode else ""
        logger.info(f"DocumentDialog opened for {document.filename}{mode_str}")

    def _create_ui(self) -> None:
        """Create UI components."""
        layout = QVBoxLayout(self)

        # Title label
        title_label = QLabel(f"📄 Document: {self.document.title or 'Untitled'}")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(title_label)

        # Filename input
        filename_layout = QHBoxLayout()
        filename_label = QLabel("Filename:")
        filename_label.setMinimumWidth(80)
        self.filename_input = QLineEdit()
        self.filename_input.setText(self.document.filename)
        self.filename_input.setPlaceholderText("document.md")
        filename_layout.addWidget(filename_label)
        filename_layout.addWidget(self.filename_input)
        layout.addLayout(filename_layout)

        # Preview area
        preview_label = QLabel("Preview:")
        preview_label.setStyleSheet("font-weight: bold; margin-top: 12px; margin-bottom: 4px;")
        layout.addWidget(preview_label)

        # Text browser for preview
        self.preview_browser = QTextBrowser()
        self.preview_browser.setReadOnly(True)
        self.preview_browser.setOpenExternalLinks(True)

        # Set CSS for code blocks and Pygments
        css = get_code_block_css(self.theme) + "\n" + get_pygments_css(
            "monokai" if self.theme == "dark" else "default"
        )
        self.preview_browser.document().setDefaultStyleSheet(css)

        # Render markdown content
        html_content = render_markdown(
            self.document.content,
            "monokai" if self.theme == "dark" else "default"
        )
        self.preview_browser.setHtml(html_content)

        # Style preview browser
        if self.theme == "dark":
            self.preview_browser.setStyleSheet("""
                QTextBrowser {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    border: 1px solid #3c3c3c;
                    border-radius: 4px;
                    padding: 12px;
                }
            """)
        else:
            self.preview_browser.setStyleSheet("""
                QTextBrowser {
                    background-color: #ffffff;
                    color: #1e1e1e;
                    border: 1px solid #d4d4d4;
                    border-radius: 4px;
                    padding: 12px;
                }
            """)

        layout.addWidget(self.preview_browser)

        # Button row
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Copy button
        self.copy_button = QPushButton("📋 Copy to Clipboard")
        self.copy_button.setMinimumWidth(150)
        self.copy_button.clicked.connect(self._on_copy_clicked)
        if self.theme == "dark":
            self.copy_button.setStyleSheet("""
                QPushButton {
                    background-color: #3c3c3c;
                    color: #d4d4d4;
                    border: 1px solid #5a5a5a;
                    border-radius: 4px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                }
            """)
        else:
            self.copy_button.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    color: #1e1e1e;
                    border: 1px solid #d4d4d4;
                    border-radius: 4px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
        button_layout.addWidget(self.copy_button)

        # Download button
        self.download_button = QPushButton("💾 Download")
        self.download_button.setMinimumWidth(150)
        self.download_button.clicked.connect(self._on_download_clicked)
        if self.theme == "dark":
            self.download_button.setStyleSheet("""
                QPushButton {
                    background-color: #0e639c;
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1177bb;
                }
            """)
        else:
            self.download_button.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
            """)
        button_layout.addWidget(self.download_button)

        # Capture button (only in source mode)
        if self.source_mode:
            self.capture_button = QPushButton("📤 Capture")
            self.capture_button.setMinimumWidth(150)
            self.capture_button.clicked.connect(self._on_capture_clicked)
            if self.theme == "dark":
                self.capture_button.setStyleSheet("""
                    QPushButton {
                        background-color: #0e639c;
                        color: #ffffff;
                        border: none;
                        border-radius: 4px;
                        padding: 8px 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #1177bb;
                    }
                """)
            else:
                self.capture_button.setStyleSheet("""
                    QPushButton {
                        background-color: #0078d4;
                        color: #ffffff;
                        border: none;
                        border-radius: 4px;
                        padding: 8px 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #106ebe;
                    }
                """)
            button_layout.addWidget(self.capture_button)

        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.setMinimumWidth(100)
        self.close_button.clicked.connect(self.close)
        if self.theme == "dark":
            self.close_button.setStyleSheet("""
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
            """)
        else:
            self.close_button.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    color: #1e1e1e;
                    border: 1px solid #d4d4d4;
                    border-radius: 4px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

    def _on_copy_clicked(self) -> None:
        """Handle copy button click."""
        content = self.document.content_with_metadata
        if copy_to_clipboard(content):
            logger.info(f"Copied document to clipboard ({len(content)} chars)")
            QMessageBox.information(
                self,
                "Copied",
                "Document content copied to clipboard!"
            )
        else:
            logger.error("Failed to copy document to clipboard")
            QMessageBox.warning(
                self,
                "Copy Failed",
                "Failed to copy document to clipboard."
            )

    def _on_download_clicked(self) -> None:
        """Handle download button click."""
        # Get filename from input
        filename = self.filename_input.text().strip()
        if not filename:
            filename = self.document.filename

        # Ensure .md extension
        if not filename.endswith('.md'):
            filename += '.md'

        # Open file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Document",
            filename,
            "Markdown Files (*.md);;All Files (*)"
        )

        if file_path:
            try:
                save_document(self.document, Path(file_path))
                logger.info(f"Saved document to {file_path}")
                QMessageBox.information(
                    self,
                    "Saved",
                    f"Document saved to:\n{file_path}"
                )
            except Exception as e:
                logger.error(f"Failed to save document: {e}")
                QMessageBox.critical(
                    self,
                    "Save Failed",
                    f"Failed to save document:\n{e}"
                )

    def _on_capture_clicked(self) -> None:
        """Handle capture button click."""
        if not self.source_context:
            logger.warning("No source context available")
            return

        # Import here to avoid circular dependency
        from ai_chat.contracts import CapturePayload, Provenance, SourceType, FormatHint

        # Create provenance
        provenance = Provenance(
            source_id="ai_chat",
            source_name="AI Chat",
            extra={"document_filename": self.document.filename}
        )

        # Create capture payload
        payload = CapturePayload(
            content=self.document.content_with_metadata,
            source_type=SourceType.DOCUMENT,
            format_hint=FormatHint.MARKDOWN,
            title=self.document.title or "Generated Document",
            provenance=provenance,
        )

        # Request capture via context callback
        try:
            self.source_context.request_capture(payload)
            logger.info(f"Captured document: {self.document.filename}")
            QMessageBox.information(
                self,
                "Captured",
                "Document captured successfully!"
            )
        except Exception as e:
            logger.error(f"Failed to capture document: {e}")
            QMessageBox.critical(
                self,
                "Capture Failed",
                f"Failed to capture document:\n{e}"
            )
