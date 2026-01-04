"""Main application entry point."""

import argparse
import asyncio
import logging
import sys

import qasync
from PyQt6.QtWidgets import QApplication

from ai_chat.config import load_config
from ai_chat.services.storage import StorageService
from ai_chat.ui import MainWindow
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

    parser.add_argument(
        "--no-storage",
        action="store_true",
        help="Disable conversation persistence (overrides config)",
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
            print(f"  Storage: {'enabled' if config.storage.enabled else 'disabled'}")
            if config.storage.enabled:
                print(f"  Data directory: {config.storage.data_directory}")
            return 0

        # Create storage service if enabled
        storage = None
        if config.storage.enabled and not args.no_storage:
            try:
                storage = StorageService(config.storage.data_directory)
                logger.info(
                    f"Storage enabled: {config.storage.data_directory}"
                )
            except Exception as e:
                logger.error(f"Failed to initialize storage: {e}")
                print(
                    f"Warning: Storage initialization failed: {e}",
                    file=sys.stderr,
                )
                print("Continuing without persistence...", file=sys.stderr)
        elif args.no_storage:
            logger.info("Storage disabled via command line")
        else:
            logger.info("Storage disabled in configuration")

        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName(config.app.title)

        # Create event loop with qasync for async support
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)

        # Create main window with optional storage
        window = MainWindow(config, storage=storage)
        window.show()

        logger.info("Application window created")

        # Run event loop with async support
        with loop:
            return loop.run_forever()

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
