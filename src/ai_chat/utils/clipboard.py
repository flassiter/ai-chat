"""Clipboard operations for copying text."""

import logging

from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


def copy_to_clipboard(text: str) -> bool:
    """
    Copy text to system clipboard.

    Args:
        text: Text to copy

    Returns:
        True if successful, False otherwise
    """
    try:
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        logger.debug(f"Copied {len(text)} characters to clipboard")
        return True
    except Exception as e:
        logger.error(f"Failed to copy to clipboard: {e}")
        return False


def get_clipboard_text() -> str:
    """
    Get text from system clipboard.

    Returns:
        Clipboard text, or empty string if none
    """
    try:
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        logger.debug(f"Retrieved {len(text)} characters from clipboard")
        return text
    except Exception as e:
        logger.error(f"Failed to get clipboard text: {e}")
        return ""
