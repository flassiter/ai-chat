"""Unit tests for clipboard utilities."""

import pytest

from ai_chat.utils.clipboard import copy_to_clipboard, get_clipboard_text


def test_copy_to_clipboard(qtbot):
    """Text copied to system clipboard."""
    test_text = "Hello, clipboard!"

    result = copy_to_clipboard(test_text)

    assert result is True
    # Verify by reading back
    clipboard_text = get_clipboard_text()
    assert clipboard_text == test_text


def test_copy_empty_string(qtbot):
    """Empty string handled gracefully."""
    result = copy_to_clipboard("")

    assert result is True
    clipboard_text = get_clipboard_text()
    assert clipboard_text == ""


def test_copy_multiline(qtbot):
    """Multiline content preserved."""
    multiline_text = """Line 1
Line 2
Line 3"""

    result = copy_to_clipboard(multiline_text)

    assert result is True
    clipboard_text = get_clipboard_text()
    assert clipboard_text == multiline_text


def test_copy_unicode(qtbot):
    """Unicode characters preserved."""
    unicode_text = "Hello 世界 🌍"

    result = copy_to_clipboard(unicode_text)

    assert result is True
    clipboard_text = get_clipboard_text()
    assert clipboard_text == unicode_text


def test_copy_large_text(qtbot):
    """Large text copied successfully."""
    large_text = "A" * 10000

    result = copy_to_clipboard(large_text)

    assert result is True
    clipboard_text = get_clipboard_text()
    assert len(clipboard_text) == 10000


def test_get_clipboard_text_empty(qtbot):
    """Get clipboard returns empty string when empty."""
    # Clear clipboard first
    copy_to_clipboard("")

    text = get_clipboard_text()

    assert text == ""


def test_round_trip(qtbot):
    """Copy and get operations work together."""
    original = "Test round trip"

    copy_to_clipboard(original)
    retrieved = get_clipboard_text()

    assert retrieved == original
