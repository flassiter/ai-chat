"""Capture payload and provenance data structures."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any

from .types import SourceType, FormatHint


@dataclass
class Provenance:
    """Provenance information for captured content."""

    source_id: str
    source_name: str
    captured_at: str = field(default_factory=lambda: datetime.now().isoformat())
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "captured_at": self.captured_at,
            **self.extra,
        }


@dataclass
class CapturePayload:
    """Payload for captured content."""

    content: str
    source_type: SourceType
    format_hint: FormatHint = FormatHint.PLAIN_TEXT
    title: Optional[str] = None
    provenance: Optional[Provenance] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            "content": self.content,
            "source_type": self.source_type.value,
            "format_hint": self.format_hint.value,
            "title": self.title,
            "metadata": self.metadata,
        }

        if self.provenance:
            result["provenance"] = self.provenance.to_dict()

        return result

    def to_markdown(self) -> str:
        """
        Convert to markdown format.

        Returns:
            Markdown representation of the capture
        """
        lines = []

        # Title
        if self.title:
            lines.append(f"# {self.title}")
            lines.append("")

        # Provenance (as comment or frontmatter)
        if self.provenance:
            lines.append("---")
            lines.append(f"source: {self.provenance.source_name}")
            lines.append(f"captured_at: {self.provenance.captured_at}")
            for key, value in self.provenance.extra.items():
                lines.append(f"{key}: {value}")
            lines.append("---")
            lines.append("")

        # Content
        if self.format_hint == FormatHint.MARKDOWN:
            lines.append(self.content)
        elif self.format_hint == FormatHint.CODE:
            lines.append("```")
            lines.append(self.content)
            lines.append("```")
        else:
            # Plain text - preserve as-is
            lines.append(self.content)

        return "\n".join(lines)
