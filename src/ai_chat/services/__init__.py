"""Service layer for AI Chat application."""

from .attachments import (
    Attachment,
    AttachmentError,
    UnsupportedFormatError,
    FileSizeError,
    create_attachment_from_file,
    create_attachment_from_bytes,
    extract_text_from_document,
    SUPPORTED_IMAGE_FORMATS,
    SUPPORTED_DOCUMENT_FORMATS,
    MAX_FILE_SIZE_MB,
)
from .chat import ChatService
from .document import (
    GeneratedDocument,
    detect_document_marker,
    extract_document_content,
    generate_filename_from_content,
    extract_title_from_content,
    add_metadata_frontmatter,
    save_document,
    can_generate_document,
)
from .storage import StorageService
from .storage_models import (
    Conversation,
    ConversationSummary,
    PersistedAttachment,
    PersistedMessage,
)

__all__ = [
    "ChatService",
    "Attachment",
    "AttachmentError",
    "UnsupportedFormatError",
    "FileSizeError",
    "create_attachment_from_file",
    "create_attachment_from_bytes",
    "extract_text_from_document",
    "SUPPORTED_IMAGE_FORMATS",
    "SUPPORTED_DOCUMENT_FORMATS",
    "MAX_FILE_SIZE_MB",
    "GeneratedDocument",
    "detect_document_marker",
    "extract_document_content",
    "generate_filename_from_content",
    "extract_title_from_content",
    "add_metadata_frontmatter",
    "save_document",
    "can_generate_document",
    "StorageService",
    "Conversation",
    "ConversationSummary",
    "PersistedAttachment",
    "PersistedMessage",
]
