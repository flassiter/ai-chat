"""Type definitions for Source plugin protocol."""

from enum import Enum


class SourceType(str, Enum):
    """Type of source content."""

    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    MIXED = "mixed"


class FormatHint(str, Enum):
    """Format hint for captured content."""

    PLAIN_TEXT = "plain_text"
    MARKDOWN = "markdown"
    HTML = "html"
    CODE = "code"
    JSON = "json"
