"""Logging configuration and setup utilities."""

import logging
import sys
from pathlib import Path
from typing import Optional

from ai_chat.config.models import LoggingConfig


def setup_logging(
    config: Optional[LoggingConfig] = None, log_level_override: Optional[str] = None
) -> None:
    """
    Configure application logging based on config and optional CLI override.

    Args:
        config: LoggingConfig object (uses defaults if None)
        log_level_override: Optional log level from CLI (takes precedence)
    """
    if config is None:
        config = LoggingConfig()

    # Determine log level (CLI override takes precedence)
    if log_level_override:
        level = log_level_override.upper()
    else:
        level = config.level

    # Convert string level to logging constant
    numeric_level = getattr(logging, level, logging.INFO)

    # Create formatter
    formatter = logging.Formatter(config.format)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler (always present)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if config.file and config.file.strip():
        file_path = Path(config.file).expanduser().resolve()

        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        root_logger.info(f"Logging to file: {file_path}")

    # Set levels for noisy third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    root_logger.info(f"Logging configured at level: {level}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for the specified module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
