"""Agent selector dropdown component."""

import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QComboBox, QWidget

from ai_chat.config.models import Config

logger = logging.getLogger(__name__)


class AgentSelector(QComboBox):
    """Dropdown for selecting AI agents."""

    agent_changed = pyqtSignal(str)  # Emits agent key

    def __init__(self, config: Config, parent: QWidget | None = None):
        """
        Initialize agent selector.

        Args:
            config: Application configuration
            parent: Parent widget
        """
        super().__init__(parent)
        self.config = config

        # Populate agents
        for agent_key, agent_config in config.agents.items():
            # Display format: [Icon] Agent Name
            icon = agent_config.icon if agent_config.icon else ""
            if icon:
                display_text = f"{icon} {agent_config.name}"
            else:
                display_text = agent_config.name

            self.addItem(display_text, userData=agent_key)

            # Set tooltip with description
            if agent_config.description:
                index = self.count() - 1
                self.setItemData(index, agent_config.description, Qt.ItemDataRole.ToolTipRole)

        # Set default agent
        default_index = self._find_agent_index(config.app.default_agent)
        if default_index >= 0:
            self.setCurrentIndex(default_index)

        # Connect signal
        self.currentIndexChanged.connect(self._on_selection_changed)

        logger.info(
            f"AgentSelector initialized with {len(config.agents)} agents, "
            f"default: {config.app.default_agent}"
        )

    def _find_agent_index(self, agent_key: str) -> int:
        """
        Find index of agent by key.

        Args:
            agent_key: Agent key to find

        Returns:
            Index, or -1 if not found
        """
        for i in range(self.count()):
            if self.itemData(i) == agent_key:
                return i
        return -1

    def _on_selection_changed(self, index: int) -> None:
        """Handle selection change."""
        if index >= 0:
            agent_key = self.itemData(index)
            logger.info(f"Agent selected: {agent_key}")
            self.agent_changed.emit(agent_key)

    def get_current_agent_key(self) -> str | None:
        """
        Get currently selected agent key.

        Returns:
            Agent key or None
        """
        return self.currentData()

    def get_current_agent_name(self) -> str | None:
        """
        Get currently selected agent display name.

        Returns:
            Agent display name or None
        """
        if self.currentIndex() >= 0:
            agent_key = self.currentData()
            return self.config.agents[agent_key].name
        return None

    def set_agent(self, agent_key: str) -> bool:
        """
        Set the selected agent by key.

        Args:
            agent_key: Agent key to select

        Returns:
            True if agent was found and selected
        """
        index = self._find_agent_index(agent_key)
        if index >= 0:
            # Block signals to prevent triggering agent_changed
            self.blockSignals(True)
            self.setCurrentIndex(index)
            self.blockSignals(False)
            logger.debug(f"Agent selector set to: {agent_key}")
            return True
        logger.warning(f"Agent not found in selector: {agent_key}")
        return False
