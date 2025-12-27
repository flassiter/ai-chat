"""Unit tests for attachment handling."""

import pytest
from pathlib import Path

from ai_chat.services.attachments import (
    Attachment,
    create_attachment_from_file,
    create_attachment_from_bytes,
    extract_text_from_document,
    validate_file_format,
    validate_file_size,
    UnsupportedFormatError,
    FileSizeError,
    MAX_FILE_SIZE_BYTES,
)


# Test data - minimal valid image headers
PNG_HEADER = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
JPEG_HEADER = b'\xff\xd8\xff\xe0' + b'\x00' * 100
GIF_HEADER = b'GIF89a' + b'\x00' * 100
WEBP_HEADER = b'RIFF' + b'\x00\x00\x00\x00' + b'WEBP' + b'\x00' * 100


def test_validate_supported_image_formats(tmp_path):
    """PNG, JPG, GIF, WebP accepted."""
    for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
        file_path = tmp_path / f"test{ext}"
        file_path.write_bytes(b"dummy data")

        result = validate_file_format(file_path)
        assert result == "image"


def test_validate_supported_document_formats(tmp_path):
    """PDF, TXT, MD accepted."""
    for ext in [".pdf", ".txt", ".md"]:
        file_path = tmp_path / f"test{ext}"
        file_path.write_bytes(b"dummy data")

        result = validate_file_format(file_path)
        assert result == "document"


def test_validate_unsupported_format(tmp_path):
    """Unsupported format raises ValidationError."""
    file_path = tmp_path / "test.exe"
    file_path.write_bytes(b"dummy data")

    with pytest.raises(UnsupportedFormatError) as exc_info:
        validate_file_format(file_path)

    assert "Unsupported file format" in str(exc_info.value)
    assert ".exe" in str(exc_info.value)


def test_validate_file_size_within_limit(tmp_path):
    """Files under 10MB accepted."""
    file_path = tmp_path / "test.png"
    # Create 1MB file
    file_path.write_bytes(b'\x00' * (1024 * 1024))

    # Should not raise
    validate_file_size(file_path)


def test_validate_file_size_exceeds_limit(tmp_path):
    """Files over 10MB rejected with clear message."""
    file_path = tmp_path / "test.png"
    # Create 11MB file
    file_path.write_bytes(b'\x00' * (11 * 1024 * 1024))

    with pytest.raises(FileSizeError) as exc_info:
        validate_file_size(file_path)

    assert "exceeds maximum" in str(exc_info.value)
    assert "10" in str(exc_info.value)


def test_create_attachment_from_file_png(tmp_path):
    """PNG file creates image attachment."""
    file_path = tmp_path / "test.png"
    file_path.write_bytes(PNG_HEADER)

    attachment = create_attachment_from_file(file_path)

    assert attachment.filename == "test.png"
    assert attachment.mime_type == "image/png"
    assert attachment.attachment_type == "image"
    assert attachment.data == PNG_HEADER


def test_create_attachment_from_file_txt(tmp_path):
    """TXT file creates document attachment."""
    file_path = tmp_path / "test.txt"
    content = b"Hello, world!"
    file_path.write_bytes(content)

    attachment = create_attachment_from_file(file_path)

    assert attachment.filename == "test.txt"
    assert attachment.mime_type == "text/plain"
    assert attachment.attachment_type == "document"
    assert attachment.data == content


def test_create_attachment_from_file_not_found(tmp_path):
    """Non-existent file raises FileNotFoundError."""
    file_path = tmp_path / "nonexistent.png"

    with pytest.raises(FileNotFoundError):
        create_attachment_from_file(file_path)


def test_create_attachment_from_bytes():
    """Attachment created from bytes."""
    data = b"test image data"
    attachment = create_attachment_from_bytes(
        data,
        "test.png",
        "image/png",
        "image"
    )

    assert attachment.filename == "test.png"
    assert attachment.mime_type == "image/png"
    assert attachment.attachment_type == "image"
    assert attachment.data == data


def test_create_attachment_from_bytes_too_large():
    """Data exceeding size limit raises FileSizeError."""
    # Create data larger than max size
    data = b'\x00' * (MAX_FILE_SIZE_BYTES + 1)

    with pytest.raises(FileSizeError):
        create_attachment_from_bytes(data, "large.png", "image/png", "image")


def test_attachment_to_base64():
    """Attachment converts to base64."""
    data = b"Hello"
    attachment = create_attachment_from_bytes(data, "test.txt", "text/plain", "document")

    b64 = attachment.to_base64()
    assert b64 == "SGVsbG8="  # Base64 of "Hello"


def test_attachment_to_data_url():
    """Attachment converts to data URL."""
    data = b"Hello"
    attachment = create_attachment_from_bytes(data, "test.txt", "text/plain", "document")

    data_url = attachment.to_data_url()
    assert data_url == "data:text/plain;base64,SGVsbG8="


def test_attachment_size_properties():
    """Size properties calculated correctly."""
    # 1MB = 1024 * 1024 bytes
    data = b'\x00' * (1024 * 1024)
    attachment = create_attachment_from_bytes(data, "test.bin", "application/octet-stream", "document")

    assert attachment.size_bytes == 1024 * 1024
    assert attachment.size_mb == pytest.approx(1.0)


def test_extract_text_from_txt_document(tmp_path):
    """Text extracted from .txt files."""
    file_path = tmp_path / "test.txt"
    content = "Hello, world!\nThis is a test."
    file_path.write_text(content)

    attachment = create_attachment_from_file(file_path)
    text = extract_text_from_document(attachment)

    assert text == content


def test_extract_text_from_md_document(tmp_path):
    """Text extracted from .md files."""
    file_path = tmp_path / "test.md"
    content = "# Heading\n\nSome **bold** text."
    file_path.write_text(content)

    attachment = create_attachment_from_file(file_path)
    text = extract_text_from_document(attachment)

    assert text == content


def test_extract_text_from_pdf_placeholder(tmp_path):
    """PDF text extraction returns placeholder."""
    file_path = tmp_path / "test.pdf"
    file_path.write_bytes(b"%PDF-1.4 dummy content")

    attachment = create_attachment_from_file(file_path)
    text = extract_text_from_document(attachment)

    # Currently returns placeholder
    assert "PDF content" in text
    assert "test.pdf" in text


def test_extract_text_from_image_raises_error(tmp_path):
    """Extracting text from image raises ValueError."""
    file_path = tmp_path / "test.png"
    file_path.write_bytes(PNG_HEADER)

    attachment = create_attachment_from_file(file_path)

    with pytest.raises(ValueError) as exc_info:
        extract_text_from_document(attachment)

    assert "not a document" in str(exc_info.value)


def test_attachment_repr():
    """Attachment has useful string representation."""
    attachment = create_attachment_from_bytes(
        b"data",
        "test.png",
        "image/png",
        "image"
    )

    # Just verify it doesn't crash
    repr_str = repr(attachment)
    assert "test.png" in repr_str or "image" in repr_str
