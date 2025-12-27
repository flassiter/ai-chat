"""Unit tests for document generation."""

import pytest
from pathlib import Path
from datetime import datetime

from ai_chat.services.document import (
    GeneratedDocument,
    detect_document_marker,
    extract_document_content,
    generate_filename_from_content,
    extract_title_from_content,
    add_metadata_frontmatter,
    save_document,
    can_generate_document,
)


def test_detect_document_marker_html_comment():
    """HTML comment marker detected correctly."""
    text = """<!-- DOCUMENT: my-doc.md -->
# My Document

This is the content.
"""
    result = detect_document_marker(text)

    assert result is not None
    filename, content = result
    assert filename == "my-doc.md"
    assert "# My Document" in content
    assert "This is the content" in content


def test_detect_document_marker_fenced_block():
    """Fenced code block with download detected."""
    text = """Here's a document:

```markdown download
# Generated Document

Some content here.
```

That's the document."""

    result = detect_document_marker(text)

    assert result is not None
    filename, content = result
    assert filename.endswith(".md")
    assert "# Generated Document" in content
    assert "Some content here" in content


def test_detect_document_marker_case_insensitive():
    """Marker detection is case insensitive."""
    text = "<!-- document: FILE.MD -->Content"
    result = detect_document_marker(text)

    assert result is not None
    assert result[0] == "FILE.MD"


def test_no_document_marker():
    """Text without markers returns None."""
    text = "Just some regular text without any document markers."
    result = detect_document_marker(text)

    assert result is None


def test_extract_document_content_with_marker():
    """Document extracted correctly from marked text."""
    text = """<!-- DOCUMENT: test.md -->
# Test Document

This is a test.
"""

    document = extract_document_content(text)

    assert document is not None
    assert document.filename == "test.md"
    assert document.title == "Test Document"
    assert "This is a test" in document.content


def test_extract_document_content_no_marker():
    """No document extracted when no marker present."""
    text = "Regular response without document."
    document = extract_document_content(text)

    assert document is None


def test_generate_filename_from_content_with_title():
    """Filename generated from first heading."""
    content = """# My Great Document

Some content here."""

    filename = generate_filename_from_content(content)

    assert filename == "my-great-document.md"


def test_generate_filename_from_content_special_chars():
    """Special characters removed from filename."""
    content = "# Hello World! (2024) & More..."

    filename = generate_filename_from_content(content)

    assert filename == "hello-world-2024-more.md"
    assert "!" not in filename
    assert "(" not in filename


def test_generate_filename_from_content_long_title():
    """Long titles truncated."""
    long_title = "a" * 100
    content = f"# {long_title}"

    filename = generate_filename_from_content(content)

    assert len(filename) <= 53  # 50 chars + ".md"


def test_generate_filename_from_content_fallback():
    """Timestamp filename when no heading."""
    content = "Just plain content without heading."

    filename = generate_filename_from_content(content)

    assert filename.startswith("document_")
    assert filename.endswith(".md")
    assert len(filename) > 15  # Has timestamp


def test_extract_title_from_content_h1():
    """Title extracted from H1 heading."""
    content = """# Main Title

Some content."""

    title = extract_title_from_content(content)

    assert title == "Main Title"


def test_extract_title_from_content_h2():
    """Title extracted from H2 heading."""
    content = """## Subtitle

Content here."""

    title = extract_title_from_content(content)

    assert title == "Subtitle"


def test_extract_title_from_content_none():
    """None returned when no heading."""
    content = "Plain text without headings."

    title = extract_title_from_content(content)

    assert title is None


def test_add_metadata_frontmatter():
    """Metadata frontmatter added correctly."""
    document = GeneratedDocument(
        content="# Test\n\nContent here.",
        filename="test.md",
        title="Test Document",
    )

    document = add_metadata_frontmatter(document, "Test Model", include_metadata=True)

    assert document.metadata is not None
    assert document.metadata["title"] == "Test Document"
    assert document.metadata["generated_by"] == "Test Model"
    assert "generated_at" in document.metadata


def test_add_metadata_frontmatter_disabled():
    """Metadata not added when disabled."""
    document = GeneratedDocument(
        content="# Test",
        filename="test.md",
    )

    document = add_metadata_frontmatter(document, "Model", include_metadata=False)

    assert document.metadata is None


def test_document_content_with_metadata():
    """Content with metadata includes YAML frontmatter."""
    document = GeneratedDocument(
        content="# Test\n\nContent",
        filename="test.md",
        title="Test",
        metadata={
            "title": "Test",
            "generated_by": "TestModel",
            "generated_at": "2024-01-01T00:00:00",
        }
    )

    content = document.content_with_metadata

    assert content.startswith("---")
    assert "title: Test" in content
    assert "generated_by: TestModel" in content
    # Timestamp with colons will be quoted in YAML
    assert "2024-01-01T00:00:00" in content
    assert "# Test" in content


def test_document_content_without_metadata():
    """Content without metadata is just content."""
    document = GeneratedDocument(
        content="# Test\n\nContent",
        filename="test.md",
    )

    content = document.content_with_metadata

    assert not content.startswith("---")
    assert content == "# Test\n\nContent"


def test_save_document(tmp_path):
    """Document saved correctly."""
    document = GeneratedDocument(
        content="# Test Document\n\nThis is a test.",
        filename="test.md",
    )

    output_path = tmp_path / "test.md"
    save_document(document, output_path)

    assert output_path.exists()
    content = output_path.read_text()
    assert "# Test Document" in content
    assert "This is a test" in content


def test_save_document_creates_directories(tmp_path):
    """Parent directories created when saving."""
    document = GeneratedDocument(
        content="Test content",
        filename="test.md",
    )

    output_path = tmp_path / "sub" / "dir" / "test.md"
    save_document(document, output_path)

    assert output_path.exists()
    assert output_path.parent.exists()


def test_save_document_with_metadata(tmp_path):
    """Document with metadata saved correctly."""
    document = GeneratedDocument(
        content="# Test",
        filename="test.md",
        metadata={"title": "Test", "author": "TestBot"},
    )

    output_path = tmp_path / "test.md"
    save_document(document, output_path)

    content = output_path.read_text()
    assert "---" in content
    assert "title: Test" in content
    assert "# Test" in content


def test_can_generate_document_true():
    """Returns true when document marker present."""
    text = "<!-- DOCUMENT: test.md -->\nContent"

    assert can_generate_document(text) is True


def test_can_generate_document_false():
    """Returns false when no marker."""
    text = "Just regular text"

    assert can_generate_document(text) is False


def test_generated_document_defaults():
    """GeneratedDocument has sensible defaults."""
    document = GeneratedDocument(
        content="Test",
        filename="test.md",
    )

    assert document.content == "Test"
    assert document.filename == "test.md"
    assert document.title is None
    assert document.format == "markdown"
    assert document.metadata is None


def test_metadata_with_colons():
    """Metadata values with colons are quoted."""
    document = GeneratedDocument(
        content="Test",
        filename="test.md",
        metadata={"time": "12:30:45"},
    )

    content = document.content_with_metadata

    # Values with colons should be quoted
    assert 'time: "12:30:45"' in content or "time: '12:30:45'" in content


def test_multiple_headings_first_used():
    """First heading used as title."""
    content = """# First Heading

Some text.

## Second Heading

More text."""

    title = extract_title_from_content(content)

    assert title == "First Heading"
