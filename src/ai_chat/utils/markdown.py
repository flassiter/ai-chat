"""Markdown rendering utilities with syntax highlighting."""

import logging
import re
from typing import Optional

import markdown
from markdown.extensions import fenced_code, tables, nl2br
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound

logger = logging.getLogger(__name__)


class CodeBlockProcessor:
    """Process code blocks with syntax highlighting."""

    def __init__(self, theme: str = "monokai"):
        """
        Initialize code block processor.

        Args:
            theme: Pygments theme name
        """
        self.theme = theme
        self.formatter = HtmlFormatter(
            style=theme,
            noclasses=False,
            cssclass="highlight",
        )
        logger.debug(f"CodeBlockProcessor initialized with theme: {theme}")

    def highlight_code(self, code: str, language: Optional[str] = None) -> str:
        """
        Apply syntax highlighting to code.

        Args:
            code: Source code to highlight
            language: Programming language (e.g., 'python', 'javascript')

        Returns:
            HTML string with syntax highlighting
        """
        try:
            if language:
                lexer = get_lexer_by_name(language, stripall=True)
            else:
                # Try to guess language
                lexer = guess_lexer(code)

            highlighted = highlight(code, lexer, self.formatter)
            logger.debug(f"Highlighted code block (language: {language or 'auto'})")
            return highlighted

        except ClassNotFound:
            logger.debug(f"No lexer found for language: {language}, using plain text")
            # Fallback to plain text
            from pygments.lexers import TextLexer
            lexer = TextLexer()
            return highlight(code, lexer, self.formatter)
        except Exception as e:
            logger.warning(f"Error highlighting code: {e}")
            # Fallback to escaped HTML
            return f'<pre><code>{_escape_html(code)}</code></pre>'


def _escape_html(text: str) -> str:
    """
    Escape HTML special characters.

    Args:
        text: Text to escape

    Returns:
        Escaped text safe for HTML
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def render_markdown(text: str, theme: str = "monokai") -> str:
    """
    Convert markdown to HTML with syntax highlighting.

    Features:
    - Headers (H1-H6)
    - Bold, italic, strikethrough
    - Links and images
    - Lists (ordered and unordered)
    - Tables
    - Fenced code blocks with syntax highlighting
    - Inline code
    - Blockquotes
    - Horizontal rules

    Args:
        text: Markdown text to render
        theme: Pygments theme for code highlighting

    Returns:
        Rendered HTML string
    """
    logger.debug(f"Rendering markdown ({len(text)} chars)")

    # Create markdown instance with extensions
    md = markdown.Markdown(
        extensions=[
            "fenced_code",
            "tables",
            "nl2br",
            "sane_lists",
        ],
        extension_configs={
            "fenced_code": {
                "lang_prefix": "language-",
            }
        },
    )

    # Convert markdown to HTML
    html = md.convert(text)

    # Post-process: apply syntax highlighting to code blocks
    processor = CodeBlockProcessor(theme=theme)
    html = _apply_syntax_highlighting(html, processor)

    logger.debug(f"Rendered HTML ({len(html)} chars)")
    return html


def _apply_syntax_highlighting(html: str, processor: CodeBlockProcessor) -> str:
    """
    Apply syntax highlighting to code blocks in HTML.

    Args:
        html: HTML with <code> blocks
        processor: CodeBlockProcessor instance

    Returns:
        HTML with highlighted code blocks
    """
    # Pattern to match: <code class="language-LANG">...</code>
    pattern = r'<code class="language-(\w+)">(.*?)</code>'

    def replace_code_block(match):
        language = match.group(1)
        code = match.group(2)
        # Unescape HTML entities
        code = code.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
        return processor.highlight_code(code, language)

    html = re.sub(pattern, replace_code_block, html, flags=re.DOTALL)

    # Also handle plain <code> blocks (inline code - no highlighting needed)
    return html


def get_pygments_css(theme: str = "monokai") -> str:
    """
    Get CSS for Pygments syntax highlighting.

    Args:
        theme: Pygments theme name

    Returns:
        CSS string
    """
    formatter = HtmlFormatter(style=theme, noclasses=False, cssclass="highlight")
    css = formatter.get_style_defs()
    logger.debug(f"Generated Pygments CSS for theme: {theme}")
    return css


def strip_markdown(text: str) -> str:
    """
    Remove markdown formatting, leaving plain text.

    Args:
        text: Markdown text

    Returns:
        Plain text without markdown formatting
    """
    # Remove headers
    text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)

    # Remove bold/italic
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"___(.+?)___", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)

    # Remove inline code
    text = re.sub(r"`(.+?)`", r"\1", text)

    # Remove links but keep text
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)

    # Remove images
    text = re.sub(r"!\[.*?\]\(.+?\)", "", text)

    # Remove code fences
    text = re.sub(r"```[\w]*\n", "", text)
    text = re.sub(r"```", "", text)

    return text.strip()
