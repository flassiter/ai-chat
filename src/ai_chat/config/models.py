"""Configuration models using Pydantic for validation."""

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ProviderType(str, Enum):
    """Type of AI provider."""

    BEDROCK = "bedrock"
    OPENAI_COMPATIBLE = "openai_compatible"


class ModelConfig(BaseModel):
    """Configuration for a single model."""

    provider: ProviderType
    name: str
    supports_images: bool = False
    supports_documents: bool = False
    supports_reasoning: bool = False
    max_tokens: int = 4096
    temperature: float = 0.7

    # Bedrock-specific fields
    model_id: Optional[str] = None
    region: Optional[str] = None
    reasoning_budget_tokens: Optional[int] = None

    # OpenAI-compatible specific fields
    base_url: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None

    @field_validator("provider", mode="before")
    @classmethod
    def validate_provider(cls, v):
        """Validate provider type."""
        if isinstance(v, str):
            try:
                return ProviderType(v)
            except ValueError:
                raise ValueError(
                    f"Invalid provider type: {v}. Must be 'bedrock' or 'openai_compatible'"
                )
        return v

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v):
        """Validate temperature is in valid range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")
        return v

    @field_validator("max_tokens")
    @classmethod
    def validate_max_tokens(cls, v):
        """Validate max_tokens is positive."""
        if v <= 0:
            raise ValueError("max_tokens must be positive")
        return v

    def model_post_init(self, __context):
        """Validate provider-specific fields after initialization."""
        if self.provider == ProviderType.BEDROCK:
            if not self.model_id:
                raise ValueError("Bedrock models require model_id")
        elif self.provider == ProviderType.OPENAI_COMPATIBLE:
            if not self.base_url:
                raise ValueError("OpenAI-compatible models require base_url")
            if not self.model:
                raise ValueError("OpenAI-compatible models require model")


class DocumentConfig(BaseModel):
    """Configuration for document generation."""

    default_directory: str = "~/Documents/AI-Exports"
    filename_template: str = "{title}_{timestamp}.md"
    include_metadata: bool = True


class LoggingConfig(BaseModel):
    """Configuration for application logging."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    file: str = ""  # Empty string means console only
    format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


class StorageConfig(BaseModel):
    """Configuration for data persistence."""

    enabled: bool = True
    data_directory: str = "./data"


class AppConfig(BaseModel):
    """General application configuration."""

    title: str = "AI Chat"
    theme: Literal["dark", "light", "system"] = "system"
    default_model: str

    @field_validator("default_model")
    @classmethod
    def validate_default_model(cls, v):
        """Validate default_model is not empty."""
        if not v or not v.strip():
            raise ValueError("default_model cannot be empty")
        return v


class Config(BaseModel):
    """Root configuration object."""

    app: AppConfig
    documents: DocumentConfig = Field(default_factory=DocumentConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    models: dict[str, ModelConfig]

    def model_post_init(self, __context):
        """Validate cross-field constraints."""
        # Ensure default_model exists in models
        if self.app.default_model not in self.models:
            available = ", ".join(self.models.keys())
            raise ValueError(
                f"default_model '{self.app.default_model}' not found in models. "
                f"Available models: {available}"
            )
