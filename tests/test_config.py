"""Unit tests for configuration system."""

import pytest
from pathlib import Path
from pydantic import ValidationError

from ai_chat.config import (
    Config,
    ModelConfig,
    ProviderType,
    LoggingConfig,
    load_config,
)


def test_load_valid_config(tmp_config_dir, valid_config_toml, write_config_file):
    """Config loads and validates correctly from valid TOML."""
    config_file = write_config_file(valid_config_toml)

    config = load_config(str(config_file))

    assert config.app.title == "Test AI Chat"
    assert config.app.default_model == "test-model"
    assert "test-model" in config.models
    assert config.models["test-model"].provider == ProviderType.OPENAI_COMPATIBLE


def test_load_invalid_provider_type(tmp_config_dir, write_config_file):
    """Invalid provider type raises ValidationError with clear message."""
    invalid_config = """
[app]
title = "Test"
default_model = "test-model"

[models.test-model]
provider = "invalid_provider"
name = "Test"
"""
    config_file = write_config_file(invalid_config)

    with pytest.raises(ValidationError) as exc_info:
        load_config(str(config_file))

    assert "Invalid provider type" in str(exc_info.value)


def test_load_missing_required_field(tmp_config_dir, write_config_file):
    """Missing required field raises ValidationError."""
    invalid_config = """
[app]
title = "Test"
default_model = "test-model"

[models.test-model]
provider = "bedrock"
name = "Test"
# Missing model_id (required for Bedrock)
"""
    config_file = write_config_file(invalid_config)

    with pytest.raises(ValidationError) as exc_info:
        load_config(str(config_file))

    assert "model_id" in str(exc_info.value).lower()


def test_config_search_path_order(tmp_path, valid_config_toml, monkeypatch):
    """Config loaded from correct path based on priority."""
    # Create config in working directory
    cwd_config = tmp_path / "config"
    cwd_config.mkdir()
    (cwd_config / "models.toml").write_text(valid_config_toml)

    # Change to temp directory
    monkeypatch.chdir(tmp_path)

    # Should load from ./config/models.toml
    config = load_config()
    assert config.app.title == "Test AI Chat"


def test_logging_config_defaults():
    """LoggingConfig uses sensible defaults when not specified."""
    logging_config = LoggingConfig()

    assert logging_config.level == "INFO"
    assert logging_config.file == ""
    assert "%(asctime)s" in logging_config.format


def test_model_config_bedrock_fields(bedrock_config_toml, tmp_config_dir, write_config_file):
    """Bedrock model config requires model_id and region."""
    config_file = write_config_file(bedrock_config_toml)
    config = load_config(str(config_file))

    bedrock_model = config.models["test-bedrock"]
    assert bedrock_model.provider == ProviderType.BEDROCK
    assert bedrock_model.model_id == "test-model-id"
    assert bedrock_model.region == "us-east-1"


def test_model_config_openai_fields(valid_config_toml, tmp_config_dir, write_config_file):
    """OpenAI-compatible config requires base_url and model."""
    config_file = write_config_file(valid_config_toml)
    config = load_config(str(config_file))

    openai_model = config.models["test-model"]
    assert openai_model.provider == ProviderType.OPENAI_COMPATIBLE
    assert openai_model.base_url == "http://localhost:11434/v1"
    assert openai_model.model == "test"


def test_invalid_default_model(tmp_config_dir, write_config_file):
    """Config validation fails when default_model doesn't exist."""
    invalid_config = """
[app]
title = "Test"
default_model = "nonexistent-model"

[models.actual-model]
provider = "openai_compatible"
name = "Actual Model"
base_url = "http://localhost:11434/v1"
model = "test"
api_key = "test"
"""
    config_file = write_config_file(invalid_config)

    with pytest.raises(ValidationError) as exc_info:
        load_config(str(config_file))

    assert "nonexistent-model" in str(exc_info.value)
    assert "actual-model" in str(exc_info.value)


def test_config_file_not_found(tmp_path, monkeypatch):
    """FileNotFoundError raised when no config file found."""
    # Change to a temp directory with no config
    monkeypatch.chdir(tmp_path)

    with pytest.raises(FileNotFoundError) as exc_info:
        load_config("/nonexistent/path/to/config.toml")

    assert "No configuration file found" in str(exc_info.value)


def test_invalid_temperature():
    """Temperature outside valid range raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        ModelConfig(
            provider=ProviderType.OPENAI_COMPATIBLE,
            name="Test",
            base_url="http://test",
            model="test",
            temperature=3.0,  # Invalid: > 2.0
        )

    assert "temperature" in str(exc_info.value).lower()


def test_invalid_max_tokens():
    """Negative or zero max_tokens raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        ModelConfig(
            provider=ProviderType.OPENAI_COMPATIBLE,
            name="Test",
            base_url="http://test",
            model="test",
            max_tokens=0,  # Invalid
        )

    assert "max_tokens" in str(exc_info.value).lower()
