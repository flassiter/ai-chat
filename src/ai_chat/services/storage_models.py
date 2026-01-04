"""Data models for persistence layer."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional
from uuid import uuid4


def generate_id() -> str:
    """Generate a UUID string."""
    return str(uuid4())


def now_iso() -> str:
    """Get current timestamp as ISO 8601 string."""
    return datetime.now().isoformat()


@dataclass
class PersistedAttachment:
    """Represents an attachment stored on filesystem."""

    id: str
    message_id: str
    filename: str
    storage_path: str  # Relative path within data directory
    mime_type: str
    attachment_type: Literal["image", "document"]
    size_bytes: int
    created_at: str

    @classmethod
    def create(
        cls,
        message_id: str,
        filename: str,
        storage_path: str,
        mime_type: str,
        attachment_type: Literal["image", "document"],
        size_bytes: int,
    ) -> "PersistedAttachment":
        """Create a new attachment with auto-generated id and timestamp."""
        return cls(
            id=generate_id(),
            message_id=message_id,
            filename=filename,
            storage_path=storage_path,
            mime_type=mime_type,
            attachment_type=attachment_type,
            size_bytes=size_bytes,
            created_at=now_iso(),
        )


@dataclass
class PersistedMessage:
    """Represents a message stored in database."""

    id: str
    conversation_id: str
    role: Literal["user", "assistant"]
    content: str
    reasoning: Optional[str]
    created_at: str
    message_order: int
    attachments: list[PersistedAttachment] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        conversation_id: str,
        role: Literal["user", "assistant"],
        content: str,
        message_order: int,
        reasoning: Optional[str] = None,
    ) -> "PersistedMessage":
        """Create a new message with auto-generated id and timestamp."""
        return cls(
            id=generate_id(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            reasoning=reasoning,
            created_at=now_iso(),
            message_order=message_order,
            attachments=[],
        )


@dataclass
class Conversation:
    """Full conversation with all messages."""

    id: str
    title: str
    model_key: str
    created_at: str
    updated_at: str
    messages: list[PersistedMessage] = field(default_factory=list)

    @classmethod
    def create(cls, title: str, model_key: str) -> "Conversation":
        """Create a new conversation with auto-generated id and timestamps."""
        now = now_iso()
        return cls(
            id=generate_id(),
            title=title,
            model_key=model_key,
            created_at=now,
            updated_at=now,
            messages=[],
        )


@dataclass
class ConversationSummary:
    """Lightweight conversation info for listing (no messages loaded)."""

    id: str
    title: str
    model_key: str
    created_at: str
    updated_at: str
    message_count: int
