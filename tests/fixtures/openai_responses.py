"""Mock OpenAI API responses for testing."""

import json


def create_sse_chunk(content: str, finish_reason: str | None = None) -> str:
    """
    Create a Server-Sent Event data chunk.

    Args:
        content: Content to include in delta
        finish_reason: Optional finish reason

    Returns:
        SSE formatted string
    """
    chunk = {
        "id": "chatcmpl-test",
        "object": "chat.completion.chunk",
        "created": 1234567890,
        "model": "test-model",
        "choices": [
            {
                "index": 0,
                "delta": {"content": content} if content else {},
                "finish_reason": finish_reason,
            }
        ],
    }

    return f"data: {json.dumps(chunk)}\n\n"


def create_sse_done_marker() -> str:
    """
    Create SSE stream end marker.

    Returns:
        SSE done marker string
    """
    return "data: [DONE]\n\n"


def mock_streaming_response() -> list[str]:
    """
    Create a mock streaming response with multiple chunks.

    Returns:
        List of SSE lines
    """
    return [
        create_sse_chunk("Hello"),
        create_sse_chunk(" world"),
        create_sse_chunk("!"),
        create_sse_chunk("", finish_reason="stop"),
        create_sse_done_marker(),
    ]


def mock_single_chunk_response() -> list[str]:
    """
    Create a mock response with a single chunk.

    Returns:
        List of SSE lines
    """
    return [
        create_sse_chunk("Complete response"),
        create_sse_chunk("", finish_reason="stop"),
        create_sse_done_marker(),
    ]


def mock_empty_response() -> list[str]:
    """
    Create a mock empty response.

    Returns:
        List of SSE lines
    """
    return [
        create_sse_chunk("", finish_reason="stop"),
        create_sse_done_marker(),
    ]
