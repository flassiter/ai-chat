"""Configuration file loader with search path support."""

import logging
import sys
from pathlib import Path
from typing import Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from pydantic import ValidationError

from .models import Config

logger = logging.getLogger(__name__)


def get_config_search_paths(custom_path: Optional[str] = None) -> list[Path]:
    """
    Get list of configuration file paths to search, in priority order.

    Args:
        custom_path: Optional custom config path (highest priority)

    Returns:
        List of Path objects to search
    """
    paths = []

    # 1. Custom path (highest priority)
    if custom_path:
        paths.append(Path(custom_path).expanduser().resolve())

    # 2. Current directory
    paths.append(Path.cwd() / "config" / "models.toml")

    # 3. User config directory
    home = Path.home()
    paths.append(home / ".config" / "ai-chat" / "models.toml")

    return paths


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load and validate configuration from TOML file.

    Searches for configuration in this order:
    1. Custom path (if provided)
    2. ./config/models.toml
    3. ~/.config/ai-chat/models.toml

    Args:
        config_path: Optional path to config file

    Returns:
        Validated Config object

    Raises:
        FileNotFoundError: If no config file found in search paths
        ValidationError: If config validation fails
        ValueError: If TOML parsing fails
    """
    search_paths = get_config_search_paths(config_path)

    # Find first existing config file
    config_file = None
    for path in search_paths:
        if path.exists():
            config_file = path
            logger.info(f"Loading configuration from: {config_file}")
            break

    if not config_file:
        search_paths_str = "\n  ".join(str(p) for p in search_paths)
        raise FileNotFoundError(
            f"No configuration file found. Searched:\n  {search_paths_str}\n\n"
            f"Create a config file at one of these locations."
        )

    # Load and parse TOML
    try:
        with open(config_file, "rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        raise ValueError(f"Failed to parse TOML from {config_file}: {e}")

    # Validate with Pydantic
    try:
        config = Config(**data)
        logger.info(
            f"Configuration loaded successfully. "
            f"{len(config.models)} models configured, "
            f"default: {config.app.default_model}"
        )
        return config
    except ValidationError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise


def save_config(config: Config, path: Path) -> None:
    """
    Save configuration to TOML file.

    Note: This is a utility function for future use.
    Currently, configuration is read-only.

    Args:
        config: Config object to save
        path: Path to save to
    """
    # For future implementation if needed
    # Would need to convert Pydantic model back to TOML
    raise NotImplementedError("Config saving not yet implemented")
