"""Reasoning detection and parsing utilities."""

import logging
import re
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def extract_reasoning_tags(text: str) -> Tuple[Optional[str], str]:
    """
    Extract reasoning content from text with <think> or <reasoning> tags.

    Supports various tag formats:
    - <think>...</think>
    - <reasoning>...</reasoning>
    - <thought>...</thought>

    Args:
        text: Text potentially containing reasoning tags

    Returns:
        Tuple of (reasoning_content, cleaned_text)
        - reasoning_content: Extracted reasoning or None
        - cleaned_text: Text with reasoning tags removed
    """
    reasoning_content = None
    cleaned_text = text

    # Patterns for different reasoning tag formats
    patterns = [
        (r"<think>(.*?)</think>", "think"),
        (r"<reasoning>(.*?)</reasoning>", "reasoning"),
        (r"<thought>(.*?)</thought>", "thought"),
    ]

    for pattern, tag_name in patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            reasoning_content = match.group(1).strip()
            # Remove the tags from the text
            cleaned_text = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE)
            logger.debug(f"Extracted {len(reasoning_content)} chars from <{tag_name}> tags")
            break

    # Clean up any extra whitespace
    cleaned_text = cleaned_text.strip()

    return reasoning_content, cleaned_text


def has_reasoning_tags(text: str) -> bool:
    """
    Check if text contains reasoning tags.

    Args:
        text: Text to check

    Returns:
        True if reasoning tags found
    """
    patterns = [
        r"<think>",
        r"<reasoning>",
        r"<thought>",
    ]

    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


def count_tokens_approximate(text: str) -> int:
    """
    Approximate token count for reasoning display.

    Uses simple heuristic: ~4 characters per token.

    Args:
        text: Text to count

    Returns:
        Approximate token count
    """
    if not text:
        return 0

    # Simple approximation: average ~4 chars per token
    # This is rough but good enough for display purposes
    return len(text) // 4


def format_reasoning_for_display(reasoning: str, max_preview_length: int = 200) -> dict:
    """
    Format reasoning content for UI display.

    Args:
        reasoning: Reasoning content
        max_preview_length: Maximum length for preview text

    Returns:
        Dict with formatted reasoning info
    """
    token_count = count_tokens_approximate(reasoning)

    # Create preview (first N characters)
    preview = reasoning[:max_preview_length]
    if len(reasoning) > max_preview_length:
        preview += "..."

    return {
        "full_text": reasoning,
        "preview": preview,
        "token_count": token_count,
        "is_truncated": len(reasoning) > max_preview_length,
    }
