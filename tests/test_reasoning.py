"""Unit tests for reasoning utilities."""

import pytest

from ai_chat.utils.reasoning import (
    extract_reasoning_tags,
    has_reasoning_tags,
    count_tokens_approximate,
    format_reasoning_for_display,
)


def test_extract_think_tags():
    """<think> tags extracted correctly."""
    text = "Let me think about this. <think>Step 1: analyze\nStep 2: conclude</think> The answer is 42."

    reasoning, cleaned = extract_reasoning_tags(text)

    assert reasoning == "Step 1: analyze\nStep 2: conclude"
    assert "<think>" not in cleaned
    assert "</think>" not in cleaned
    assert "The answer is 42" in cleaned


def test_extract_reasoning_tags():
    """<reasoning> tags extracted correctly."""
    text = "Before answering: <reasoning>First consider X, then Y</reasoning> Final answer."

    reasoning, cleaned = extract_reasoning_tags(text)

    assert reasoning == "First consider X, then Y"
    assert "<reasoning>" not in cleaned
    assert "Final answer" in cleaned


def test_extract_thought_tags():
    """<thought> tags extracted correctly."""
    text = "<thought>Internal monologue here</thought>External response"

    reasoning, cleaned = extract_reasoning_tags(text)

    assert reasoning == "Internal monologue here"
    assert "External response" in cleaned


def test_no_reasoning_tags():
    """Text without tags returns None for reasoning."""
    text = "Just plain text without any reasoning tags"

    reasoning, cleaned = extract_reasoning_tags(text)

    assert reasoning is None
    assert cleaned == text


def test_nested_content_preserved():
    """Nested content within tags preserved."""
    text = "<think>Line 1\n\nLine 2 with **markdown**\n\nLine 3</think>Response"

    reasoning, cleaned = extract_reasoning_tags(text)

    assert "Line 1" in reasoning
    assert "Line 2 with **markdown**" in reasoning
    assert "Line 3" in reasoning
    assert "Response" in cleaned


def test_case_insensitive():
    """Tags are case insensitive."""
    text = "<THINK>Capital tags</THINK> result"

    reasoning, cleaned = extract_reasoning_tags(text)

    assert reasoning == "Capital tags"
    assert "result" in cleaned


def test_has_reasoning_tags_think():
    """Detect <think> tags."""
    assert has_reasoning_tags("<think>content</think>")
    assert has_reasoning_tags("prefix <think>content</think> suffix")
    assert not has_reasoning_tags("no tags here")


def test_has_reasoning_tags_reasoning():
    """Detect <reasoning> tags."""
    assert has_reasoning_tags("<reasoning>content</reasoning>")


def test_has_reasoning_tags_thought():
    """Detect <thought> tags."""
    assert has_reasoning_tags("<thought>content</thought>")


def test_count_tokens_approximate():
    """Token counting approximation."""
    # Approximately 4 characters per token
    text = "a" * 100
    tokens = count_tokens_approximate(text)

    assert tokens == 25  # 100 / 4


def test_count_tokens_empty():
    """Empty string has zero tokens."""
    assert count_tokens_approximate("") == 0
    assert count_tokens_approximate(None) == 0


def test_format_reasoning_for_display_short():
    """Short reasoning doesn't get truncated."""
    reasoning = "This is short reasoning"

    formatted = format_reasoning_for_display(reasoning)

    assert formatted["full_text"] == reasoning
    assert formatted["preview"] == reasoning
    assert not formatted["is_truncated"]
    assert formatted["token_count"] > 0


def test_format_reasoning_for_display_long():
    """Long reasoning gets truncated in preview."""
    reasoning = "a" * 300

    formatted = format_reasoning_for_display(reasoning, max_preview_length=100)

    assert formatted["full_text"] == reasoning
    assert len(formatted["preview"]) <= 103  # 100 + "..."
    assert formatted["is_truncated"]
    assert "..." in formatted["preview"]


def test_multiple_tags_only_first_extracted():
    """Only first tag set extracted."""
    text = "<think>First</think> middle <think>Second</think> end"

    reasoning, cleaned = extract_reasoning_tags(text)

    # Only first set should be extracted
    assert reasoning == "First"
    assert "<think>Second</think>" not in cleaned or "Second" in cleaned


def test_whitespace_handling():
    """Extra whitespace cleaned up."""
    text = "   <think>  reasoning  </think>   response   "

    reasoning, cleaned = extract_reasoning_tags(text)

    assert reasoning == "reasoning"
    assert cleaned == "response"
