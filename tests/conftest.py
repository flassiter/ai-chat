"""Shared pytest fixtures for all tests."""

import pytest
from pathlib import Path


@pytest.fixture
def tmp_config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def valid_config_toml():
    """Return content for a valid minimal configuration."""
    return """
[app]
title = "Test AI Chat"
theme = "dark"
default_model = "test-model"

[documents]
default_directory = "~/test-docs"
filename_template = "{title}_{timestamp}.md"
include_metadata = true

[logging]
level = "INFO"
file = ""
format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

[models.test-model]
provider = "openai_compatible"
name = "Test Model"
base_url = "http://localhost:11434/v1"
model = "test"
api_key = "test"
supports_images = false
supports_documents = false
supports_reasoning = false
max_tokens = 4096
temperature = 0.7
"""


@pytest.fixture
def bedrock_config_toml():
    """Return content for a Bedrock model configuration."""
    return """
[app]
title = "Test AI Chat"
theme = "dark"
default_model = "test-bedrock"

[models.test-bedrock]
provider = "bedrock"
name = "Test Bedrock Model"
model_id = "test-model-id"
region = "us-east-1"
supports_images = true
supports_documents = false
supports_reasoning = false
max_tokens = 8192
temperature = 0.7
"""


@pytest.fixture
def write_config_file(tmp_config_dir):
    """Factory fixture to write config content to file."""

    def _write(content: str, filename: str = "models.toml") -> Path:
        file_path = tmp_config_dir / filename
        file_path.write_text(content)
        return file_path

    return _write
