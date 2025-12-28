"""Unit tests for AIChatSource plugin."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QTextCursor

from ai_chat.source import AIChatSource
from ai_chat.contracts import (
    SourceContext,
    CapturePayload,
    SourceType,
    FormatHint,
)


@pytest.fixture
def mock_context():
    """Create a mock SourceContext."""
    return SourceContext(
        request_capture=Mock(),
        notify_status=Mock(),
        get_config=Mock(return_value=None),
    )


@pytest.fixture
def source():
    """Create an AIChatSource instance."""
    return AIChatSource()


class TestAIChatSourceProperties:
    """Tests for AIChatSource properties."""

    def test_source_id(self, source):
        """source_id returns 'ai_chat'."""
        assert source.source_id == "ai_chat"

    def test_display_name(self, source):
        """display_name returns 'AI Chat'."""
        assert source.display_name == "AI Chat"

    def test_icon(self, source):
        """icon returns path or None."""
        icon = source.icon
        # Icon may or may not exist depending on setup
        assert icon is None or isinstance(icon, str)

    def test_capabilities(self, source):
        """Capabilities correctly set for selection and full capture."""
        caps = source.capabilities

        assert caps["supports_selection"] is True
        assert caps["supports_full_capture"] is True
        assert caps["supports_streaming"] is False
        assert caps["supports_attachments"] is False


class TestAIChatSourceWidget:
    """Tests for widget creation."""

    @patch("ai_chat.source.load_config")
    @patch("ai_chat.source.ChatWidget")
    def test_create_widget_returns_qwidget(self, mock_chat_widget, mock_load_config, source, mock_context, qtbot):
        """create_widget returns a QWidget instance."""
        # Setup mocks
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        mock_widget_instance = Mock(spec=QWidget)
        mock_chat_widget.return_value = mock_widget_instance

        # Create widget
        widget = source.create_widget(mock_context)

        # Verify ChatWidget was created with correct parameters
        mock_chat_widget.assert_called_once_with(
            mock_config,
            source_mode=True,
            source_context=mock_context
        )
        assert widget == mock_widget_instance

    @patch("ai_chat.source.load_config")
    @patch("ai_chat.source.ChatWidget")
    def test_create_widget_stores_context(self, mock_chat_widget, mock_load_config, source, mock_context):
        """Context stored for later use."""
        # Setup mocks
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        mock_widget_instance = Mock(spec=QWidget)
        mock_chat_widget.return_value = mock_widget_instance

        # Create widget
        source.create_widget(mock_context)

        # Verify context was stored
        assert source._context == mock_context
        assert source._widget == mock_widget_instance


class TestAIChatSourceSelection:
    """Tests for get_selection method."""

    @patch("ai_chat.source.load_config")
    @patch("ai_chat.source.ChatWidget")
    def test_get_selection_no_selection(self, mock_chat_widget, mock_load_config, source, mock_context):
        """get_selection returns None when nothing selected."""
        # Setup mocks
        mock_config = Mock()
        mock_load_config.return_value = mock_config

        # Create mock widget with no selection
        mock_widget = Mock()
        mock_text_cursor = Mock(spec=QTextCursor)
        mock_text_cursor.selectedText.return_value = ""
        mock_widget.chat_display.text_browser.textCursor.return_value = mock_text_cursor
        mock_widget.chat_service.get_current_model_name.return_value = "test-model"
        mock_chat_widget.return_value = mock_widget

        # Create widget and try to get selection
        source.create_widget(mock_context)
        result = source.get_selection()

        assert result is None

    @patch("ai_chat.source.load_config")
    @patch("ai_chat.source.ChatWidget")
    def test_get_selection_with_selection(self, mock_chat_widget, mock_load_config, source, mock_context):
        """get_selection returns CapturePayload with selected text."""
        # Setup mocks
        mock_config = Mock()
        mock_load_config.return_value = mock_config

        # Create mock widget with selection
        mock_widget = Mock()
        mock_text_cursor = Mock(spec=QTextCursor)
        mock_text_cursor.selectedText.return_value = "Selected text content"
        mock_widget.chat_display.text_browser.textCursor.return_value = mock_text_cursor
        mock_widget.chat_service.get_current_model_name.return_value = "test-model"
        mock_chat_widget.return_value = mock_widget

        # Create widget and get selection
        source.create_widget(mock_context)
        result = source.get_selection()

        # Verify result
        assert isinstance(result, CapturePayload)
        assert result.content == "Selected text content"
        assert result.source_type == SourceType.TEXT
        assert result.format_hint == FormatHint.PLAIN_TEXT
        assert result.title == "AI Chat Selection"
        assert result.provenance is not None
        assert result.provenance.source_id == "ai_chat"
        assert result.provenance.source_name == "AI Chat"
        assert result.provenance.extra["model"] == "test-model"
        assert result.provenance.extra["selection"] is True

    def test_get_selection_no_widget(self, source):
        """get_selection returns None when widget not created yet."""
        result = source.get_selection()
        assert result is None


class TestAIChatSourceFullCapture:
    """Tests for get_full_capture method."""

    @patch("ai_chat.source.load_config")
    @patch("ai_chat.source.ChatWidget")
    def test_get_full_capture_no_response(self, mock_chat_widget, mock_load_config, source, mock_context):
        """get_full_capture returns None when no AI response."""
        # Setup mocks
        mock_config = Mock()
        mock_load_config.return_value = mock_config

        # Create mock widget with no response
        mock_widget = Mock()
        mock_widget.chat_display.get_last_assistant_message.return_value = None
        mock_chat_widget.return_value = mock_widget

        # Create widget and try to get full capture
        source.create_widget(mock_context)
        result = source.get_full_capture()

        assert result is None

    @patch("ai_chat.source.load_config")
    @patch("ai_chat.source.ChatWidget")
    def test_get_full_capture_with_response(self, mock_chat_widget, mock_load_config, source, mock_context):
        """get_full_capture returns last AI response as CapturePayload."""
        # Setup mocks
        mock_config = Mock()
        mock_load_config.return_value = mock_config

        # Create mock widget with response
        mock_widget = Mock()
        mock_widget.chat_display.get_last_assistant_message.return_value = "# AI Response\n\nThis is the response."
        mock_widget.chat_display.message_count = 5
        mock_widget.chat_service.get_current_model_name.return_value = "test-model"
        mock_chat_widget.return_value = mock_widget

        # Create widget and get full capture
        source.create_widget(mock_context)
        result = source.get_full_capture()

        # Verify result
        assert isinstance(result, CapturePayload)
        assert result.content == "# AI Response\n\nThis is the response."
        assert result.source_type == SourceType.TEXT
        assert result.format_hint == FormatHint.MARKDOWN
        assert result.title == "AI Chat Response"
        assert result.provenance is not None
        assert result.provenance.source_id == "ai_chat"
        assert result.provenance.source_name == "AI Chat"
        assert result.provenance.extra["model"] == "test-model"
        assert result.provenance.extra["message_count"] == 5

    def test_get_full_capture_no_widget(self, source):
        """get_full_capture returns None when widget not created yet."""
        result = source.get_full_capture()
        assert result is None


class TestAIChatSourceShutdown:
    """Tests for shutdown method."""

    @patch("ai_chat.source.load_config")
    @patch("ai_chat.source.ChatWidget")
    def test_shutdown_clears_resources(self, mock_chat_widget, mock_load_config, source, mock_context):
        """shutdown clears widget and context."""
        # Setup mocks
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        mock_widget = Mock()
        mock_chat_widget.return_value = mock_widget

        # Create widget
        source.create_widget(mock_context)
        assert source._widget is not None
        assert source._context is not None

        # Shutdown
        source.shutdown()

        # Verify resources cleared
        assert source._widget is None
        assert source._context is None

    def test_shutdown_when_no_widget(self, source):
        """shutdown works even when no widget created."""
        # Should not raise an error
        source.shutdown()
        assert source._widget is None
        assert source._context is None
