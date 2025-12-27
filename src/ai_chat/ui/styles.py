"""UI styling and themes."""

import logging
from typing import Literal

logger = logging.getLogger(__name__)

ThemeType = Literal["dark", "light"]


def get_chat_display_style(theme: ThemeType = "dark") -> str:
    """
    Get QSS stylesheet for chat display.

    Args:
        theme: Theme type ('dark' or 'light')

    Returns:
        QSS stylesheet string
    """
    if theme == "dark":
        return """
            QTextBrowser {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                selection-background-color: #264f78;
            }
        """
    else:  # light theme
        return """
            QTextBrowser {
                background-color: #ffffff;
                color: #1e1e1e;
                border: 1px solid #d4d4d4;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                selection-background-color: #add6ff;
            }
        """


def get_input_widget_style(theme: ThemeType = "dark") -> str:
    """
    Get QSS stylesheet for input widget.

    Args:
        theme: Theme type ('dark' or 'light')

    Returns:
        QSS stylesheet string
    """
    if theme == "dark":
        return """
            QTextEdit {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                selection-background-color: #264f78;
            }
            QPushButton {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
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
        """
    else:  # light theme
        return """
            QTextEdit {
                background-color: #ffffff;
                color: #1e1e1e;
                border: 1px solid #d4d4d4;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                selection-background-color: #add6ff;
            }
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
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
        """


def get_message_html(content: str, role: Literal["user", "assistant"], theme: ThemeType = "dark") -> str:
    """
    Generate HTML for a chat message with styling.

    Args:
        content: Message content (already rendered HTML from markdown)
        role: Message role ('user' or 'assistant')
        theme: Theme type

    Returns:
        Styled HTML string
    """
    if theme == "dark":
        if role == "user":
            bg_color = "#0e639c"
            text_color = "#ffffff"
            label = "You"
        else:
            bg_color = "#2d2d2d"
            text_color = "#d4d4d4"
            label = "AI"
    else:  # light theme
        if role == "user":
            bg_color = "#0078d4"
            text_color = "#ffffff"
            label = "You"
        else:
            bg_color = "#f5f5f5"
            text_color = "#1e1e1e"
            label = "AI"

    return f"""
        <div style="margin: 12px 0; padding: 12px; background-color: {bg_color};
                    border-radius: 8px; color: {text_color};">
            <div style="font-weight: bold; margin-bottom: 8px; font-size: 13px; opacity: 0.8;">
                {label}
            </div>
            <div style="line-height: 1.6;">
                {content}
            </div>
        </div>
    """


def get_error_html(message: str, theme: ThemeType = "dark") -> str:
    """
    Generate HTML for an error message.

    Args:
        message: Error message text
        theme: Theme type

    Returns:
        Styled HTML string
    """
    if theme == "dark":
        bg_color = "#5a1d1d"
        text_color = "#f48771"
    else:
        bg_color = "#fde7e9"
        text_color = "#a80000"

    return f"""
        <div style="margin: 12px 0; padding: 12px; background-color: {bg_color};
                    border-radius: 8px; color: {text_color}; border-left: 4px solid {text_color};">
            <div style="font-weight: bold; margin-bottom: 4px;">
                ⚠ Error
            </div>
            <div>
                {message}
            </div>
        </div>
    """


def get_code_block_css(theme: ThemeType = "dark") -> str:
    """
    Get CSS for code blocks (complements Pygments CSS).

    Args:
        theme: Theme type

    Returns:
        CSS string
    """
    if theme == "dark":
        return """
            pre {
                background-color: #1e1e1e;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 12px;
                overflow-x: auto;
                margin: 12px 0;
            }
            code {
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 13px;
                background-color: #2d2d2d;
                padding: 2px 6px;
                border-radius: 3px;
            }
            pre code {
                background-color: transparent;
                padding: 0;
            }
            .highlight {
                background-color: #1e1e1e;
                border-radius: 4px;
            }
        """
    else:
        return """
            pre {
                background-color: #f5f5f5;
                border: 1px solid #d4d4d4;
                border-radius: 4px;
                padding: 12px;
                overflow-x: auto;
                margin: 12px 0;
            }
            code {
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 13px;
                background-color: #e8e8e8;
                padding: 2px 6px;
                border-radius: 3px;
            }
            pre code {
                background-color: transparent;
                padding: 0;
            }
            .highlight {
                background-color: #f5f5f5;
                border-radius: 4px;
            }
        """


def get_copy_button_style(theme: ThemeType = "dark") -> str:
    """
    Get QSS for copy button.

    Args:
        theme: Theme type

    Returns:
        QSS string
    """
    if theme == "dark":
        return """
            QPushButton {
                background-color: #3c3c3c;
                color: #d4d4d4;
                border: 1px solid #5a5a5a;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #6e6e6e;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
            }
        """
    else:
        return """
            QPushButton {
                background-color: #f0f0f0;
                color: #1e1e1e;
                border: 1px solid #d4d4d4;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #b0b0b0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """
