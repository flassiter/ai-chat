"""Unit tests for contracts layer."""

import pytest
from datetime import datetime

from ai_chat.contracts import (
    CapturePayload,
    Provenance,
    SourceContext,
    SourceCapabilities,
    SourceType,
    FormatHint,
)


class TestSourceType:
    """Tests for SourceType enum."""

    def test_source_type_enum(self):
        """SourceType enum has expected values."""
        assert SourceType.TEXT == "text"
        assert SourceType.IMAGE == "image"
        assert SourceType.DOCUMENT == "document"
        assert SourceType.MIXED == "mixed"


class TestFormatHint:
    """Tests for FormatHint enum."""

    def test_format_hint_enum(self):
        """FormatHint enum has expected values."""
        assert FormatHint.PLAIN_TEXT == "plain_text"
        assert FormatHint.MARKDOWN == "markdown"
        assert FormatHint.HTML == "html"
        assert FormatHint.CODE == "code"
        assert FormatHint.JSON == "json"


class TestProvenance:
    """Tests for Provenance dataclass."""

    def test_provenance_creation(self):
        """Provenance created with required fields."""
        provenance = Provenance(
            source_id="test_source",
            source_name="Test Source",
        )

        assert provenance.source_id == "test_source"
        assert provenance.source_name == "Test Source"
        assert isinstance(provenance.captured_at, str)
        assert provenance.extra == {}

    def test_provenance_extra_field(self):
        """Extra metadata stored in provenance."""
        provenance = Provenance(
            source_id="test_source",
            source_name="Test Source",
            extra={"model": "claude-3", "temperature": 0.7}
        )

        assert provenance.extra == {"model": "claude-3", "temperature": 0.7}

    def test_provenance_to_dict(self):
        """Provenance converts to dict correctly."""
        provenance = Provenance(
            source_id="test_source",
            source_name="Test Source",
            extra={"model": "claude-3"}
        )

        result = provenance.to_dict()

        assert result["source_id"] == "test_source"
        assert result["source_name"] == "Test Source"
        assert "captured_at" in result
        assert result["model"] == "claude-3"

    def test_provenance_custom_timestamp(self):
        """Provenance accepts custom timestamp."""
        timestamp = "2024-01-01T12:00:00"
        provenance = Provenance(
            source_id="test_source",
            source_name="Test Source",
            captured_at=timestamp
        )

        assert provenance.captured_at == timestamp


class TestCapturePayload:
    """Tests for CapturePayload dataclass."""

    def test_capture_payload_creation(self):
        """CapturePayload created with required fields."""
        payload = CapturePayload(
            content="Test content",
            source_type=SourceType.TEXT,
        )

        assert payload.content == "Test content"
        assert payload.source_type == SourceType.TEXT
        assert payload.format_hint == FormatHint.PLAIN_TEXT
        assert payload.title is None
        assert payload.provenance is None
        assert payload.metadata == {}

    def test_capture_payload_with_provenance(self):
        """CapturePayload can include provenance."""
        provenance = Provenance(
            source_id="test_source",
            source_name="Test Source",
        )
        payload = CapturePayload(
            content="Test content",
            source_type=SourceType.TEXT,
            provenance=provenance,
        )

        assert payload.provenance == provenance

    def test_capture_payload_to_dict(self):
        """CapturePayload converts to dict correctly."""
        provenance = Provenance(
            source_id="test_source",
            source_name="Test Source",
        )
        payload = CapturePayload(
            content="Test content",
            source_type=SourceType.TEXT,
            format_hint=FormatHint.MARKDOWN,
            title="Test Title",
            provenance=provenance,
            metadata={"key": "value"}
        )

        result = payload.to_dict()

        assert result["content"] == "Test content"
        assert result["source_type"] == "text"
        assert result["format_hint"] == "markdown"
        assert result["title"] == "Test Title"
        assert "provenance" in result
        assert result["metadata"] == {"key": "value"}

    def test_capture_payload_to_markdown_basic(self):
        """CapturePayload converts to markdown correctly."""
        payload = CapturePayload(
            content="Test content",
            source_type=SourceType.TEXT,
            title="Test Title",
        )

        result = payload.to_markdown()

        assert "# Test Title" in result
        assert "Test content" in result

    def test_capture_payload_to_markdown_with_provenance(self):
        """CapturePayload includes provenance in markdown frontmatter."""
        provenance = Provenance(
            source_id="test_source",
            source_name="Test Source",
        )
        payload = CapturePayload(
            content="Test content",
            source_type=SourceType.TEXT,
            title="Test Title",
            provenance=provenance,
        )

        result = payload.to_markdown()

        assert "---" in result  # YAML frontmatter delimiters
        assert "source: Test Source" in result
        assert "captured_at:" in result
        assert "Test content" in result

    def test_capture_payload_to_markdown_no_title(self):
        """CapturePayload to markdown works without title."""
        payload = CapturePayload(
            content="Test content",
            source_type=SourceType.TEXT,
        )

        result = payload.to_markdown()

        assert "Test content" in result


class TestSourceCapabilities:
    """Tests for SourceCapabilities dataclass."""

    def test_source_capabilities_defaults(self):
        """SourceCapabilities has correct defaults."""
        caps = SourceCapabilities()

        assert caps.supports_selection is False
        assert caps.supports_full_capture is True  # Default is True
        assert caps.supports_streaming is False
        assert caps.supports_attachments is False

    def test_source_capabilities_custom(self):
        """SourceCapabilities accepts custom values."""
        caps = SourceCapabilities(
            supports_selection=True,
            supports_full_capture=True,
            supports_streaming=False,
            supports_attachments=True,
        )

        assert caps.supports_selection is True
        assert caps.supports_full_capture is True
        assert caps.supports_streaming is False
        assert caps.supports_attachments is True


class TestSourceContext:
    """Tests for SourceContext dataclass."""

    def test_source_context_creation(self):
        """SourceContext created with callbacks."""
        def request_capture(payload):
            pass

        def notify_status(message):
            pass

        def get_config(key):
            return None

        context = SourceContext(
            request_capture=request_capture,
            notify_status=notify_status,
            get_config=get_config,
        )

        assert context.request_capture == request_capture
        assert context.notify_status == notify_status
        assert context.get_config == get_config

    def test_source_context_validates_request_capture(self):
        """SourceContext validates request_capture is callable."""
        with pytest.raises(ValueError, match="request_capture must be callable"):
            SourceContext(
                request_capture="not callable",
                notify_status=lambda m: None,
                get_config=lambda k: None,
            )

    def test_source_context_validates_notify_status(self):
        """SourceContext validates notify_status is callable."""
        with pytest.raises(ValueError, match="notify_status must be callable"):
            SourceContext(
                request_capture=lambda p: None,
                notify_status="not callable",
                get_config=lambda k: None,
            )

    def test_source_context_validates_get_config(self):
        """SourceContext validates get_config is callable."""
        with pytest.raises(ValueError, match="get_config must be callable"):
            SourceContext(
                request_capture=lambda p: None,
                notify_status=lambda m: None,
                get_config="not callable",
            )
