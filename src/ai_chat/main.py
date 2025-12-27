"""Main application entry point."""

import argparse
import logging
import sys

from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow

from ai_chat.config import load_config
from ai_chat.utils import setup_logging

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AI Chat - Chat interface for local and AWS Bedrock AI models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (default: searches ./config/models.toml, ~/.config/ai-chat/models.toml)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Override log level from config",
    )

    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Validate configuration and exit",
    )

    return parser.parse_args()


def main() -> int:
    """Main application entry point."""
    args = parse_args()

    try:
        # Load configuration
        config = load_config(args.config)

        # Setup logging (before other components)
        setup_logging(config.logging, args.log_level)

        logger.info(f"Starting {config.app.title}")
        logger.info(f"Default model: {config.app.default_model}")
        logger.debug(f"Configuration: {len(config.models)} models configured")

        # If just validating config, exit
        if args.validate_config:
            print("Configuration is valid!")
            print(f"  App: {config.app.title}")
            print(f"  Models: {len(config.models)}")
            print(f"  Default: {config.app.default_model}")
            print(f"  Theme: {config.app.theme}")
            print(f"  Log level: {config.logging.level}")
            return 0

        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName(config.app.title)

        # Create main window (placeholder for now)
        window = QMainWindow()
        window.setWindowTitle(config.app.title)
        window.setMinimumSize(800, 600)

        # Placeholder content
        label = QLabel("AI Chat - Phase 1 Foundation\n\nConfiguration loaded successfully!")
        label.setStyleSheet("QLabel { font-size: 16px; padding: 20px; }")
        window.setCentralWidget(label)

        window.show()

        logger.info("Application window created")

        # Run event loop
        return app.exec()

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.log_level == "DEBUG":
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
