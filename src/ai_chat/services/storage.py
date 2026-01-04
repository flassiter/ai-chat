"""Storage service for persisting conversations and attachments."""

import logging
import mimetypes
import shutil
import sqlite3
from pathlib import Path
from typing import Optional

from ai_chat.services.storage_models import (
    Conversation,
    ConversationSummary,
    PersistedAttachment,
    PersistedMessage,
    generate_id,
    now_iso,
)

logger = logging.getLogger(__name__)


class StorageService:
    """Service for persisting conversations to SQLite and attachments to filesystem."""

    def __init__(self, data_directory: str):
        """
        Initialize storage service.

        Args:
            data_directory: Path to data directory (e.g., "./data")
        """
        self.data_dir = Path(data_directory).expanduser().resolve()
        self.db_path = self.data_dir / "chat.db"
        self.attachments_dir = self.data_dir / "attachments"

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.attachments_dir.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        logger.info(f"StorageService initialized: {self.data_dir}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self) -> None:
        """Create database tables if they don't exist."""
        schema = """
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            model_key TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            reasoning TEXT,
            created_at TEXT NOT NULL,
            message_order INTEGER NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS attachments (
            id TEXT PRIMARY KEY,
            message_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            storage_path TEXT NOT NULL,
            mime_type TEXT NOT NULL,
            attachment_type TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_messages_conversation
            ON messages(conversation_id, message_order);
        CREATE INDEX IF NOT EXISTS idx_attachments_message
            ON attachments(message_id);
        CREATE INDEX IF NOT EXISTS idx_conversations_updated
            ON conversations(updated_at DESC);
        """

        with self._get_connection() as conn:
            conn.executescript(schema)
            logger.debug("Database schema initialized")

    # === Conversation Operations ===

    def create_conversation(self, title: str, model_key: str) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation.create(title=title, model_key=model_key)

        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO conversations (id, title, model_key, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    conversation.id,
                    conversation.title,
                    conversation.model_key,
                    conversation.created_at,
                    conversation.updated_at,
                ),
            )

        # Create attachments subdirectory
        (self.attachments_dir / conversation.id).mkdir(exist_ok=True)

        logger.info(f"Created conversation: {conversation.id} - {title}")
        return conversation

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Load a conversation with all messages and attachments."""
        with self._get_connection() as conn:
            # Get conversation
            row = conn.execute(
                "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone()

            if not row:
                return None

            conversation = Conversation(
                id=row["id"],
                title=row["title"],
                model_key=row["model_key"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                messages=[],
            )

            # Get messages
            msg_rows = conn.execute(
                """SELECT * FROM messages
                   WHERE conversation_id = ?
                   ORDER BY message_order""",
                (conversation_id,),
            ).fetchall()

            for msg_row in msg_rows:
                message = PersistedMessage(
                    id=msg_row["id"],
                    conversation_id=msg_row["conversation_id"],
                    role=msg_row["role"],
                    content=msg_row["content"],
                    reasoning=msg_row["reasoning"],
                    created_at=msg_row["created_at"],
                    message_order=msg_row["message_order"],
                    attachments=[],
                )

                # Get attachments for this message
                att_rows = conn.execute(
                    "SELECT * FROM attachments WHERE message_id = ?", (message.id,)
                ).fetchall()

                for att_row in att_rows:
                    attachment = PersistedAttachment(
                        id=att_row["id"],
                        message_id=att_row["message_id"],
                        filename=att_row["filename"],
                        storage_path=att_row["storage_path"],
                        mime_type=att_row["mime_type"],
                        attachment_type=att_row["attachment_type"],
                        size_bytes=att_row["size_bytes"],
                        created_at=att_row["created_at"],
                    )
                    message.attachments.append(attachment)

                conversation.messages.append(message)

            logger.debug(
                f"Loaded conversation: {conversation_id} "
                f"({len(conversation.messages)} messages)"
            )
            return conversation

    def list_conversations(self) -> list[ConversationSummary]:
        """List all conversations (most recent first)."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT c.*, COUNT(m.id) as message_count
                   FROM conversations c
                   LEFT JOIN messages m ON m.conversation_id = c.id
                   GROUP BY c.id
                   ORDER BY c.updated_at DESC"""
            ).fetchall()

            summaries = [
                ConversationSummary(
                    id=row["id"],
                    title=row["title"],
                    model_key=row["model_key"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    message_count=row["message_count"],
                )
                for row in rows
            ]

            logger.debug(f"Listed {len(summaries)} conversations")
            return summaries

    def update_conversation_title(self, conversation_id: str, title: str) -> None:
        """Update conversation title."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                (title, now_iso(), conversation_id),
            )
        logger.debug(f"Updated conversation title: {conversation_id} -> {title}")

    def delete_conversation(self, conversation_id: str) -> None:
        """Delete conversation and all associated files."""
        # Delete attachment files first
        attachments_path = self.attachments_dir / conversation_id
        if attachments_path.exists():
            shutil.rmtree(attachments_path)
            logger.debug(f"Deleted attachments directory: {attachments_path}")

        # Delete from database (CASCADE handles messages and attachment records)
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM conversations WHERE id = ?", (conversation_id,)
            )

        logger.info(f"Deleted conversation: {conversation_id}")

    # === Message Operations ===

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        reasoning: Optional[str] = None,
        images: Optional[list[bytes]] = None,
        documents: Optional[list[tuple[str, bytes]]] = None,
    ) -> PersistedMessage:
        """Add a message to a conversation with optional attachments."""
        with self._get_connection() as conn:
            # Get next message order
            result = conn.execute(
                "SELECT COALESCE(MAX(message_order), -1) + 1 FROM messages "
                "WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
            message_order = result[0]

            # Create message
            message = PersistedMessage.create(
                conversation_id=conversation_id,
                role=role,
                content=content,
                message_order=message_order,
                reasoning=reasoning,
            )

            # Insert message
            conn.execute(
                """INSERT INTO messages
                   (id, conversation_id, role, content, reasoning, created_at, message_order)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    message.id,
                    message.conversation_id,
                    message.role,
                    message.content,
                    message.reasoning,
                    message.created_at,
                    message.message_order,
                ),
            )

            # Update conversation timestamp
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now_iso(), conversation_id),
            )

            # Save image attachments
            if images:
                for i, image_data in enumerate(images):
                    attachment = self._save_attachment(
                        conn,
                        conversation_id,
                        message.id,
                        f"image_{i}.png",
                        image_data,
                        "image/png",
                        "image",
                    )
                    message.attachments.append(attachment)

            # Save document attachments
            if documents:
                for filename, doc_data in documents:
                    # Guess MIME type from filename
                    mime_type, _ = mimetypes.guess_type(filename)
                    mime_type = mime_type or "application/octet-stream"

                    attachment = self._save_attachment(
                        conn,
                        conversation_id,
                        message.id,
                        filename,
                        doc_data,
                        mime_type,
                        "document",
                    )
                    message.attachments.append(attachment)

        logger.debug(
            f"Added message to {conversation_id}: {role} "
            f"({len(message.attachments)} attachments)"
        )
        return message

    def _save_attachment(
        self,
        conn: sqlite3.Connection,
        conversation_id: str,
        message_id: str,
        filename: str,
        data: bytes,
        mime_type: str,
        attachment_type: str,
    ) -> PersistedAttachment:
        """Save attachment to filesystem and database."""
        # Generate unique storage path
        unique_id = generate_id()[:8]
        safe_filename = "".join(
            c if c.isalnum() or c in "._-" else "_" for c in filename
        )
        storage_path = f"attachments/{conversation_id}/{unique_id}_{safe_filename}"

        # Write file
        full_path = self.data_dir / storage_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(data)

        # Create attachment record
        attachment = PersistedAttachment.create(
            message_id=message_id,
            filename=filename,
            storage_path=storage_path,
            mime_type=mime_type,
            attachment_type=attachment_type,
            size_bytes=len(data),
        )

        # Insert into database
        conn.execute(
            """INSERT INTO attachments
               (id, message_id, filename, storage_path, mime_type,
                attachment_type, size_bytes, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                attachment.id,
                attachment.message_id,
                attachment.filename,
                attachment.storage_path,
                attachment.mime_type,
                attachment.attachment_type,
                attachment.size_bytes,
                attachment.created_at,
            ),
        )

        logger.debug(f"Saved attachment: {storage_path}")
        return attachment

    def load_attachment_data(self, attachment: PersistedAttachment) -> bytes:
        """Load attachment data from filesystem."""
        full_path = self.data_dir / attachment.storage_path
        return full_path.read_bytes()

    # === Utility ===

    def generate_title_from_message(self, content: str, max_length: int = 50) -> str:
        """Generate a conversation title from the first user message."""
        # Take first line or first N characters
        title = content.split("\n")[0].strip()
        if len(title) > max_length:
            title = title[: max_length - 3] + "..."
        return title or "New Conversation"
