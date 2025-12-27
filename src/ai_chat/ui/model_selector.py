"""Model selector dropdown component."""

import logging

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QWidget

from ai_chat.config.models import Config

logger = logging.getLogger(__name__)


class ModelSelector(QComboBox):
    """Dropdown for selecting AI models."""

    model_changed = pyqtSignal(str)  # Emits model key

    def __init__(self, config: Config, parent: QWidget | None = None):
        """
        Initialize model selector.

        Args:
            config: Application configuration
            parent: Parent widget
        """
        super().__init__(parent)
        self.config = config

        # Populate models
        for model_key, model_config in config.models.items():
            # Display format: [Provider] Model Name
            provider_name = model_config.provider.value.replace("_", " ").title()
            display_text = f"[{provider_name}] {model_config.name}"

            self.addItem(display_text, userData=model_key)

        # Set default model
        default_index = self._find_model_index(config.app.default_model)
        if default_index >= 0:
            self.setCurrentIndex(default_index)

        # Connect signal
        self.currentIndexChanged.connect(self._on_selection_changed)

        logger.info(
            f"ModelSelector initialized with {len(config.models)} models, "
            f"default: {config.app.default_model}"
        )

    def _find_model_index(self, model_key: str) -> int:
        """
        Find index of model by key.

        Args:
            model_key: Model key to find

        Returns:
            Index, or -1 if not found
        """
        for i in range(self.count()):
            if self.itemData(i) == model_key:
                return i
        return -1

    def _on_selection_changed(self, index: int) -> None:
        """Handle selection change."""
        if index >= 0:
            model_key = self.itemData(index)
            logger.info(f"Model selected: {model_key}")
            self.model_changed.emit(model_key)

    def get_current_model_key(self) -> str | None:
        """
        Get currently selected model key.

        Returns:
            Model key or None
        """
        return self.currentData()

    def get_current_model_name(self) -> str | None:
        """
        Get currently selected model display name.

        Returns:
            Model display name or None
        """
        if self.currentIndex() >= 0:
            model_key = self.currentData()
            return self.config.models[model_key].name
        return None
