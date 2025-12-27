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
]
