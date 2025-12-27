# AI Chat Application

Chat interface for local and AWS Bedrock AI models.

## Features

- **Multi-Provider Support**: Chat with local OpenAI-compatible models (Ollama, LM Studio, llama.cpp) and AWS Bedrock models
- **Streaming Responses**: Real-time streaming of AI responses
- **Markdown Rendering**: Beautiful rendering of markdown with syntax-highlighted code blocks
- **Document Generation**: Automatic detection and export of AI-generated documents
- **Dual Mode**: Standalone desktop application or embeddable Source plugin
- **Configurable Logging**: Full logging support with configurable levels and output

## Installation

### From Source

```bash
# Clone the repository
cd ai-chat

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Quick Start

1. **Configure your models** in `config/models.toml`
2. **Run the application**:

```bash
ai-chat
```

## Command Line Options

```bash
ai-chat --help                    # Show help
ai-chat --config path/to/config   # Use custom config file
ai-chat --log-level DEBUG         # Set log level
ai-chat --validate-config         # Validate configuration and exit
```

## Configuration

Configuration is loaded from (in priority order):
1. Custom path specified with `--config`
2. `./config/models.toml`
3. `~/.config/ai-chat/models.toml`

### Example Configuration

```toml
[app]
title = "AI Chat"
theme = "dark"
default_model = "ollama-mistral"

[logging]
level = "INFO"
file = ""  # Optional log file path

[models.ollama-mistral]
provider = "openai_compatible"
name = "Mistral (Ollama)"
base_url = "http://localhost:11434/v1"
model = "mistral"
api_key = "ollama"
supports_images = false
supports_documents = false
max_tokens = 4096
temperature = 0.7

[models.bedrock-claude]
provider = "bedrock"
name = "Claude 3.5 Sonnet"
model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
region = "us-east-1"
supports_images = true
supports_documents = true
max_tokens = 8192
```

## Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=ai_chat --cov-report=html

# Run specific test file
pytest tests/test_config.py -v
```

### Project Structure

```
ai-chat/
├── config/                 # Configuration files
├── src/ai_chat/           # Main application code
│   ├── config/            # Configuration system
│   ├── providers/         # AI provider implementations
│   ├── services/          # Business logic services
│   ├── ui/                # Qt UI components
│   ├── utils/             # Utilities (logging, etc.)
│   └── main.py            # Application entry point
└── tests/                 # Test suite
```

## Requirements

- Python 3.10+
- PyQt6 6.6.0+
- For AWS Bedrock: AWS credentials configured
- For local models: Running model server (Ollama, LM Studio, etc.)

## License

MIT

## Development Status

**Phase 1**: ✅ Complete (Foundation, Configuration, Logging)
- Project structure
- Configuration system with TOML
- Logging infrastructure
- Base provider interface
- CLI entry point
- Test framework

**Phase 2**: Minimal Chat with Ollama (In Progress)
**Phase 3**: Enhanced Chat Experience (Planned)
**Phase 4**: AWS Bedrock Integration (Planned)
**Phase 5**: Reasoning/Chain-of-Thought Display (Planned)
**Phase 6**: Attachments & Media (Planned)
**Phase 7**: Document Generation (Planned)
**Phase 8**: Source Plugin Mode (Planned)
