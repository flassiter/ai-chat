"""Attachment handling for images and documents."""

import base64
import logging
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

logger = logging.getLogger(__name__)

# Supported formats
SUPPORTED_IMAGE_FORMATS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
SUPPORTED_DOCUMENT_FORMATS = {".pdf", ".txt", ".md"}
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@dataclass
class Attachment:
    """Represents a file attachment (image or document)."""

    filename: str
    mime_type: str
    data: bytes
    attachment_type: Literal["image", "document"]

    @property
    def size_bytes(self) -> int:
        """Get size in bytes."""
        return len(self.data)

    @property
    def size_mb(self) -> float:
        """Get size in megabytes."""
        return self.size_bytes / (1024 * 1024)

    def to_base64(self) -> str:
        """Convert data to base64 string."""
        return base64.b64encode(self.data).decode("utf-8")

    def to_data_url(self) -> str:
        """Convert to data URL for embedding."""
        b64_data = self.to_base64()
        return f"data:{self.mime_type};base64,{b64_data}"


class AttachmentError(Exception):
    """Base exception for attachment-related errors."""

    pass


class UnsupportedFormatError(AttachmentError):
    """Raised when file format is not supported."""

    pass


class FileSizeError(AttachmentError):
    """Raised when file size exceeds limit."""

    pass


def validate_file_format(file_path: Path) -> Literal["image", "document"]:
    """
    Validate file format is supported.

    Args:
        file_path: Path to file

    Returns:
        Attachment type ('image' or 'document')

    Raises:
        UnsupportedFormatError: If format not supported
    """
    suffix = file_path.suffix.lower()

    if suffix in SUPPORTED_IMAGE_FORMATS:
        logger.debug(f"Validated image format: {suffix}")
        return "image"
    elif suffix in SUPPORTED_DOCUMENT_FORMATS:
        logger.debug(f"Validated document format: {suffix}")
        return "document"
    else:
        supported = SUPPORTED_IMAGE_FORMATS | SUPPORTED_DOCUMENT_FORMATS
        raise UnsupportedFormatError(
            f"Unsupported file format '{suffix}'. Supported formats: {', '.join(sorted(supported))}"
        )


def validate_file_size(file_path: Path) -> None:
    """
    Validate file size is within limits.

    Args:
        file_path: Path to file

    Raises:
        FileSizeError: If file exceeds size limit
    """
    size_bytes = file_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    if size_bytes > MAX_FILE_SIZE_BYTES:
        logger.warning(f"File too large: {size_mb:.2f}MB (max {MAX_FILE_SIZE_MB}MB)")
        raise FileSizeError(
            f"File size {size_mb:.2f}MB exceeds maximum of {MAX_FILE_SIZE_MB}MB"
        )

    logger.debug(f"Validated file size: {size_mb:.2f}MB")


def create_attachment_from_file(file_path: Path) -> Attachment:
    """
    Create attachment from file path.

    Args:
        file_path: Path to file

    Returns:
        Attachment object

    Raises:
        UnsupportedFormatError: If format not supported
        FileSizeError: If file too large
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Validate format
    attachment_type = validate_file_format(file_path)

    # Validate size
    validate_file_size(file_path)

    # Read file data
    with open(file_path, "rb") as f:
        data = f.read()

    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        # Fallback based on extension
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".md": "text/markdown",
        }
        mime_type = mime_map.get(file_path.suffix.lower(), "application/octet-stream")

    attachment = Attachment(
        filename=file_path.name,
        mime_type=mime_type,
        data=data,
        attachment_type=attachment_type,
    )

    logger.info(
        f"Created {attachment_type} attachment: {attachment.filename} "
        f"({attachment.size_mb:.2f}MB, {mime_type})"
    )

    return attachment


def create_attachment_from_bytes(
    data: bytes,
    filename: str,
    mime_type: str,
    attachment_type: Literal["image", "document"],
) -> Attachment:
    """
    Create attachment from bytes (e.g., clipboard paste).

    Args:
        data: File data
        filename: Filename
        mime_type: MIME type
        attachment_type: Type of attachment

    Returns:
        Attachment object

    Raises:
        FileSizeError: If data exceeds size limit
    """
    size_bytes = len(data)
    size_mb = size_bytes / (1024 * 1024)

    if size_bytes > MAX_FILE_SIZE_BYTES:
        logger.warning(f"Data too large: {size_mb:.2f}MB (max {MAX_FILE_SIZE_MB}MB)")
        raise FileSizeError(
            f"Data size {size_mb:.2f}MB exceeds maximum of {MAX_FILE_SIZE_MB}MB"
        )

    attachment = Attachment(
        filename=filename,
        mime_type=mime_type,
        data=data,
        attachment_type=attachment_type,
    )

    logger.info(
        f"Created {attachment_type} attachment from bytes: {filename} "
        f"({attachment.size_mb:.2f}MB, {mime_type})"
    )

    return attachment


def extract_text_from_document(attachment: Attachment) -> str:
    """
    Extract text content from document attachment.

    Args:
        attachment: Document attachment

    Returns:
        Extracted text

    Raises:
        ValueError: If attachment is not a document or format not supported
    """
    if attachment.attachment_type != "document":
        raise ValueError(f"Attachment is not a document: {attachment.attachment_type}")

    # Text and Markdown files
    if attachment.mime_type in ("text/plain", "text/markdown"):
        try:
            text = attachment.data.decode("utf-8")
            logger.debug(f"Extracted {len(text)} characters from {attachment.filename}")
            return text
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode text file: {e}")
            raise ValueError(f"Failed to decode text file: {e}")

    # PDF files - placeholder for now
    elif attachment.mime_type == "application/pdf":
        logger.warning("PDF text extraction not yet implemented")
        return f"[PDF content: {attachment.filename}]"

    else:
        raise ValueError(f"Unsupported document type: {attachment.mime_type}")
