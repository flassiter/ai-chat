"""Unit tests for markdown utilities."""

import pytest

from ai_chat.utils.markdown import (
    render_markdown,
    strip_markdown,
    get_pygments_css,
)


def test_render_headers():
    """H1-H6 headers render as correct HTML tags."""
    markdown = """# Header 1
## Header 2
### Header 3"""

    html = render_markdown(markdown)

    assert "<h1>Header 1</h1>" in html
    assert "<h2>Header 2</h2>" in html
    assert "<h3>Header 3</h3>" in html


def test_render_code_block_with_language():
    """Fenced code block with language gets syntax highlighting."""
    markdown = """```python
def hello():
    print("Hello, World!")
```"""

    html = render_markdown(markdown)

    # Should contain code block
    assert "hello" in html
    assert "print" in html
    # Pygments should add highlighting divs
    assert "highlight" in html.lower()


def test_render_code_block_no_language():
    """Fenced code block without language renders as code."""
    markdown = """```
plain text code
no highlighting
```"""

    html = render_markdown(markdown)

    assert "plain text code" in html
    assert "no highlighting" in html


def test_render_inline_code():
    """Inline `code` renders correctly."""
    markdown = "This is `inline code` in text."

    html = render_markdown(markdown)

    assert "<code>" in html
    assert "inline code" in html


def test_render_lists():
    """Ordered and unordered lists render correctly."""
    markdown = """- Item 1
- Item 2
- Item 3

1. First
2. Second
3. Third"""

    html = render_markdown(markdown)

    assert "<ul>" in html
    assert "<li>Item 1</li>" in html
    assert "<ol>" in html
    assert "<li>First</li>" in html


def test_render_tables():
    """Markdown tables render as HTML tables."""
    markdown = """| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |"""

    html = render_markdown(markdown)

    assert "<table>" in html
    assert "<thead>" in html
    assert "<tbody>" in html
    assert "Header 1" in html
    assert "Cell 1" in html


def test_render_links():
    """Links render as clickable anchors."""
    markdown = "[Click here](https://example.com)"

    html = render_markdown(markdown)

    assert "<a" in html
    assert 'href="https://example.com"' in html
    assert "Click here" in html


def test_render_bold_italic():
    """Bold and italic formatting renders correctly."""
    markdown = "**bold text** and *italic text* and ***both***"

    html = render_markdown(markdown)

    assert "<strong>bold text</strong>" in html
    assert "<em>italic text</em>" in html


def test_render_empty_string():
    """Empty string returns empty HTML."""
    html = render_markdown("")
    assert html == ""


def test_render_plain_text():
    """Plain text without markdown renders as-is."""
    text = "Just plain text"
    html = render_markdown(text)

    assert "Just plain text" in html


def test_strip_markdown_headers():
    """Strip markdown removes header markers."""
    markdown = "# Header"
    plain = strip_markdown(markdown)

    assert plain == "Header"
    assert "#" not in plain


def test_strip_markdown_bold():
    """Strip markdown removes bold markers."""
    markdown = "This is **bold** text"
    plain = strip_markdown(markdown)

    assert plain == "This is bold text"
    assert "**" not in plain


def test_strip_markdown_italic():
    """Strip markdown removes italic markers."""
    markdown = "This is *italic* text"
    plain = strip_markdown(markdown)

    assert plain == "This is italic text"
    assert "*" not in plain


def test_strip_markdown_code():
    """Strip markdown removes inline code markers."""
    markdown = "This is `code` text"
    plain = strip_markdown(markdown)

    assert plain == "This is code text"
    assert "`" not in plain


def test_strip_markdown_links():
    """Strip markdown removes link syntax but keeps text."""
    markdown = "[Click here](https://example.com)"
    plain = strip_markdown(markdown)

    assert plain == "Click here"
    assert "http" not in plain


def test_strip_markdown_code_fence():
    """Strip markdown removes code fences."""
    markdown = """```python
code here
```"""
    plain = strip_markdown(markdown)

    assert "```" not in plain
    assert "code here" in plain


def test_get_pygments_css_dark():
    """Pygments CSS generates for dark theme."""
    css = get_pygments_css("monokai")

    assert len(css) > 0
    assert ".highlight" in css


def test_get_pygments_css_light():
    """Pygments CSS generates for light theme."""
    css = get_pygments_css("default")

    assert len(css) > 0
    assert ".highlight" in css
