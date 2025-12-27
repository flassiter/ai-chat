"""Mock Bedrock API responses for testing."""


def mock_bedrock_stream_response() -> dict:
    """
    Create a mock Bedrock converse_stream response.

    Returns:
        Mock response dict with stream generator
    """

    def stream_generator():
        """Generate Bedrock stream events."""
        # Content block start
        yield {
            "contentBlockStart": {
                "start": {"text": ""},
                "contentBlockIndex": 0,
            }
        }

        # Content deltas (the actual response text)
        yield {
            "contentBlockDelta": {
                "delta": {"text": "Hello"},
                "contentBlockIndex": 0,
            }
        }

        yield {
            "contentBlockDelta": {
                "delta": {"text": " from"},
                "contentBlockIndex": 0,
            }
        }

        yield {
            "contentBlockDelta": {
                "delta": {"text": " Bedrock!"},
                "contentBlockIndex": 0,
            }
        }

        # Content block stop
        yield {
            "contentBlockStop": {
                "contentBlockIndex": 0,
            }
        }

        # Metadata with stop reason
        yield {
            "metadata": {
                "usage": {
                    "inputTokens": 10,
                    "outputTokens": 5,
                    "totalTokens": 15,
                },
                "stopReason": "end_turn",
            }
        }

        # Message stop
        yield {
            "messageStop": {
                "stopReason": "end_turn",
            }
        }

    return {"stream": stream_generator()}


def mock_bedrock_single_chunk() -> dict:
    """
    Create a mock Bedrock response with single chunk.

    Returns:
        Mock response dict
    """

    def stream_generator():
        yield {
            "contentBlockDelta": {
                "delta": {"text": "Complete response"},
                "contentBlockIndex": 0,
            }
        }
        yield {
            "messageStop": {
                "stopReason": "end_turn",
            }
        }

    return {"stream": stream_generator()}


def mock_bedrock_empty_response() -> dict:
    """
    Create a mock empty Bedrock response.

    Returns:
        Mock response dict
    """

    def stream_generator():
        yield {
            "messageStop": {
                "stopReason": "end_turn",
            }
        }

    return {"stream": stream_generator()}


def mock_bedrock_error_response() -> dict:
    """
    Create a mock Bedrock error response.

    Returns:
        Mock response dict with error
    """

    def stream_generator():
        yield {
            "error": {
                "message": "Stream processing error",
                "code": "InternalError",
            }
        }

    return {"stream": stream_generator()}
