"""Document generation and extraction service."""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class GeneratedDocument:
    """Represents a generated document from AI response."""

    content: str
    filename: str
    title: Optional[str] = None
    format: str = "markdown"
    metadata: Optional[dict] = None

    @property
    def content_with_metadata(self) -> str:
        """Get content with optional YAML frontmatter."""
        if not self.metadata:
            return self.content

        # Build YAML frontmatter
        lines = ["---"]
        for key, value in self.metadata.items():
            # Escape string values with quotes if needed
            if isinstance(value, str) and (":" in value or "\n" in value):
                value = f'"{value}"'
            lines.append(f"{key}: {value}")
        lines.append("---")
        lines.append("")
        lines.append(self.content)

        return "\n".join(lines)


def detect_document_marker(text: str) -> Optional[tuple[str, str]]:
    """
    Detect document marker in text.

    Looks for patterns like:
    - <!-- DOCUMENT: filename.md -->
    - ```markdown download

    Args:
        text: Text to search

    Returns:
        Tuple of (filename, content) if found, None otherwise
    """
    # Pattern 1: HTML comment marker
    # <!-- DOCUMENT: filename.md -->
    comment_pattern = r"<!--\s*DOCUMENT:\s*([^\s]+)\s*-->"
    comment_match = re.search(comment_pattern, text, re.IGNORECASE)

    if comment_match:
        filename = comment_match.group(1).strip()
        # Extract content after the marker
        content_start = comment_match.end()
        content = text[content_start:].strip()

        logger.debug(f"Detected document marker: {filename}")
        return (filename, content)

    # Pattern 2: Fenced code block with download marker
    # ```markdown download
    fence_pattern = r"```(?:markdown|md)\s+download\s*\n(.*?)```"
    fence_match = re.search(fence_pattern, text, re.DOTALL | re.IGNORECASE)

    if fence_match:
        content = fence_match.group(1).strip()
        # Try to extract filename from first heading
        filename = generate_filename_from_content(content)

        logger.debug(f"Detected fenced download block: {filename}")
        return (filename, content)

    return None


def extract_document_content(text: str) -> Optional[GeneratedDocument]:
    """
    Extract document content from AI response.

    Args:
        text: AI response text

    Returns:
        GeneratedDocument if document detected, None otherwise
    """
    detection = detect_document_marker(text)

    if not detection:
        logger.debug("No document marker detected")
        return None

    filename, content = detection

    # Extract title from first heading if present
    title = extract_title_from_content(content)

    # Create document
    document = GeneratedDocument(
        content=content,
        filename=filename,
        title=title,
        format="markdown",
    )

    logger.info(f"Extracted document: {filename} (title: {title})")
    return document


def generate_filename_from_content(content: str) -> str:
    """
    Generate filename from content.

    Tries to extract from first heading, otherwise uses timestamp.

    Args:
        content: Document content

    Returns:
        Generated filename
    """
    title = extract_title_from_content(content)

    if title:
        # Convert title to filename
        # Remove special characters, replace spaces with dashes
        filename = re.sub(r'[^\w\s-]', '', title)
        filename = re.sub(r'[\s_]+', '-', filename)
        filename = filename.lower().strip('-')
        # Limit length
        filename = filename[:50]
        return f"{filename}.md"

    # Fallback to timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"document_{timestamp}.md"


def extract_title_from_content(content: str) -> Optional[str]:
    """
    Extract title from first markdown heading.

    Args:
        content: Markdown content

    Returns:
        Title if found, None otherwise
    """
    # Look for first heading (# or ##)
    heading_pattern = r"^#{1,2}\s+(.+)$"
    match = re.search(heading_pattern, content, re.MULTILINE)

    if match:
        title = match.group(1).strip()
        logger.debug(f"Extracted title: {title}")
        return title

    return None


def add_metadata_frontmatter(
    document: GeneratedDocument,
    model_name: str,
    include_metadata: bool = True,
) -> GeneratedDocument:
    """
    Add YAML frontmatter with provenance metadata.

    Args:
        document: Document to add metadata to
        model_name: Name of model that generated document
        include_metadata: Whether to include metadata

    Returns:
        Document with metadata added
    """
    if not include_metadata:
        return document

    # Build metadata
    metadata = {
        "title": document.title or "Untitled Document",
        "generated_by": model_name,
        "generated_at": datetime.now().isoformat(),
        "format": "markdown",
    }

    # Update document
    document.metadata = metadata

    logger.debug(f"Added metadata frontmatter to {document.filename}")
    return document


def save_document(document: GeneratedDocument, output_path: Path) -> None:
    """
    Save document to file.

    Args:
        document: Document to save
        output_path: Path to save to

    Raises:
        IOError: If save fails
    """
    try:
        # Create parent directories if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content with metadata
        content = document.content_with_metadata
        output_path.write_text(content, encoding="utf-8")

        logger.info(f"Saved document to {output_path} ({len(content)} chars)")

    except Exception as e:
        logger.error(f"Failed to save document to {output_path}: {e}")
        raise IOError(f"Failed to save document: {e}") from e


def can_generate_document(response_text: str) -> bool:
    """
    Check if response contains a document that can be generated.

    Args:
        response_text: AI response text

    Returns:
        True if document can be generated
    """
    return detect_document_marker(response_text) is not None
