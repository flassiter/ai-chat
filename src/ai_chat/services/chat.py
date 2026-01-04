"""Chat service for managing conversations and routing to providers."""

import logging
from typing import AsyncIterator, Optional

from ai_chat.config.models import AgentConfig, Config, ModelConfig
from ai_chat.providers import BaseProvider, Message, StreamChunk, create_provider
from ai_chat.services.knowledge import KnowledgeService
from ai_chat.services.storage import StorageService

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat conversations."""

    def __init__(
        self,
        config: Config,
        storage: Optional[StorageService] = None,
        knowledge_service: Optional[KnowledgeService] = None,
    ):
        """
        Initialize chat service with configuration.

        Args:
            config: Application configuration
            storage: Optional storage service for persistence
            knowledge_service: Optional knowledge service for agent knowledge
        """
        self.config = config
        self.storage = storage
        self.knowledge_service = knowledge_service or KnowledgeService()
        self.messages: list[Message] = []
        self.current_model_key: str = config.app.default_model
        self.current_agent_key: str = config.app.default_agent

        # Current conversation tracking (for persistence)
        self._conversation_id: Optional[str] = None
        self._conversation_title_set: bool = False

        logger.info(
            f"ChatService initialized with default model: {self.current_model_key}, "
            f"default agent: {self.current_agent_key}"
        )

    @property
    def conversation_id(self) -> Optional[str]:
        """Get current conversation ID."""
        return self._conversation_id

    def new_conversation(self) -> Optional[str]:
        """
        Start a new conversation.

        Returns:
            Conversation ID if persistence enabled, None otherwise
        """
        self.messages.clear()
        self._conversation_id = None
        self._conversation_title_set = False

        if self.storage:
            # Create new conversation with placeholder title
            conv = self.storage.create_conversation(
                title="New Conversation",
                model_key=self.current_model_key,
            )
            self._conversation_id = conv.id
            logger.info(f"Created new conversation: {conv.id}")
            return conv.id

        return None

    def load_conversation(self, conversation_id: str) -> bool:
        """
        Load an existing conversation.

        Args:
            conversation_id: ID of conversation to load

        Returns:
            True if loaded successfully
        """
        if not self.storage:
            logger.warning("Cannot load conversation: no storage configured")
            return False

        conversation = self.storage.get_conversation(conversation_id)
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
            return False

        # Clear current state
        self.messages.clear()

        # Rebuild in-memory messages from persisted messages
        for pm in conversation.messages:
            # Load attachment data
            images = []
            documents = []
            for att in pm.attachments:
                data = self.storage.load_attachment_data(att)
                if att.attachment_type == "image":
                    images.append(data)
                else:
                    documents.append((att.filename, data))

            message = Message(
                role=pm.role,
                content=pm.content,
                images=images,
                documents=documents,
            )
            self.messages.append(message)

        self._conversation_id = conversation_id
        self._conversation_title_set = True  # Existing conversations have titles
        self.current_model_key = conversation.model_key

        logger.info(
            f"Loaded conversation: {conversation_id} ({len(self.messages)} messages)"
        )
        return True

    def add_message(
        self,
        role: str,
        content: str,
        images: Optional[list[bytes]] = None,
        documents: Optional[list[tuple[str, bytes]]] = None,
        reasoning: Optional[str] = None,
    ) -> None:
        """
        Add a message to the conversation history.

        Args:
            role: "user" or "assistant"
            content: Message content
            images: Optional list of image data (bytes)
            documents: Optional list of (filename, data) tuples
            reasoning: Optional reasoning content (for assistant messages)
        """
        message = Message(
            role=role,
            content=content,
            images=images or [],
            documents=documents or [],
        )
        self.messages.append(message)

        # Persist if storage is configured
        if self.storage and self._conversation_id:
            self.storage.add_message(
                conversation_id=self._conversation_id,
                role=role,
                content=content,
                reasoning=reasoning,
                images=images,
                documents=documents,
            )

            # Auto-generate title from first user message
            if role == "user" and not self._conversation_title_set:
                title = self.storage.generate_title_from_message(content)
                self.storage.update_conversation_title(self._conversation_id, title)
                self._conversation_title_set = True
                logger.debug(f"Set conversation title: {title}")

        # Logging
        attachment_info = []
        if images:
            attachment_info.append(f"{len(images)} image(s)")
        if documents:
            attachment_info.append(f"{len(documents)} document(s)")
        attachment_str = (
            f" with {', '.join(attachment_info)}" if attachment_info else ""
        )

        logger.info(
            f"Added {role} message to history{attachment_str} "
            f"(total: {len(self.messages)})"
        )
        logger.debug(f"Message content: {content[:100]}...")

    def clear_history(self) -> None:
        """Clear all conversation history (starts new conversation if persisting)."""
        message_count = len(self.messages)
        self.messages.clear()

        # Start new conversation if storage enabled
        if self.storage:
            self.new_conversation()
        else:
            self._conversation_id = None
            self._conversation_title_set = False

        logger.info(f"Cleared conversation history ({message_count} messages)")

    def set_model(self, model_key: str) -> None:
        """
        Set the active model.

        Args:
            model_key: Key of model in config

        Raises:
            ValueError: If model_key not found
        """
        if model_key not in self.config.models:
            available = ", ".join(self.config.models.keys())
            raise ValueError(
                f"Model '{model_key}' not found. Available: {available}"
            )

        self.current_model_key = model_key
        logger.info(f"Switched to model: {model_key}")

    def get_current_model_config(self) -> ModelConfig:
        """
        Get configuration for currently selected model.

        Returns:
            ModelConfig for current model
        """
        return self.config.models[self.current_model_key]

    def get_current_model_name(self) -> str:
        """
        Get display name of currently selected model.

        Returns:
            Model display name
        """
        return self.config.models[self.current_model_key].name

    def set_agent(self, agent_key: str) -> None:
        """
        Set the active agent.

        Args:
            agent_key: Key of agent in config

        Raises:
            ValueError: If agent_key not found
        """
        if agent_key not in self.config.agents:
            available = ", ".join(self.config.agents.keys())
            raise ValueError(f"Agent '{agent_key}' not found. Available: {available}")

        self.current_agent_key = agent_key
        logger.info(f"Switched to agent: {agent_key}")

    def get_current_agent_config(self) -> AgentConfig:
        """
        Get configuration for currently selected agent.

        Returns:
            AgentConfig for current agent
        """
        return self.config.agents[self.current_agent_key]

    def get_current_agent_name(self) -> str:
        """
        Get display name of currently selected agent.

        Returns:
            Agent display name
        """
        return self.config.agents[self.current_agent_key].name

    async def _build_messages_with_agent(
        self,
        user_message: str,
    ) -> list[Message]:
        """
        Build message list with agent instructions and knowledge.

        Args:
            user_message: The current user message

        Returns:
            List of messages including system message with agent context
        """
        agent = self.get_current_agent_config()
        messages_to_send = []

        # Build system prompt if agent has instructions
        if agent.instructions:
            system_content = agent.instructions

            # Fetch relevant knowledge if enabled
            if agent.inject_knowledge_automatically and agent.knowledge_sources:
                knowledge_parts = await self.knowledge_service.fetch_relevant_knowledge(
                    user_message, agent, max_sources=3
                )
                if knowledge_parts:
                    knowledge_text = "\n\n".join(
                        [
                            f"### Reference: {name}\n{content}"
                            for name, content in knowledge_parts
                        ]
                    )
                    system_content += f"\n\n## Relevant Knowledge\n\n{knowledge_text}"
                    logger.debug(
                        f"Injected {len(knowledge_parts)} knowledge source(s) into system prompt"
                    )

            # Add system message
            messages_to_send.append(
                Message(role="system", content=system_content)
            )
            logger.debug(f"Added system prompt ({len(system_content)} chars)")

        # Add existing conversation history
        messages_to_send.extend(self.messages)

        return messages_to_send

    def _create_provider(self, model_config: ModelConfig) -> BaseProvider:
        """
        Create provider instance for model config using factory.

        Args:
            model_config: Model configuration

        Returns:
            Provider instance

        Raises:
            ValueError: If provider type not supported
        """
        return create_provider(model_config)

    async def stream_response(
        self,
        user_message: str,
        images: Optional[list[bytes]] = None,
        documents: Optional[list[tuple[str, bytes]]] = None,
    ) -> AsyncIterator[StreamChunk]:
        """
        Send user message and stream AI response.

        Args:
            user_message: User's message
            images: Optional list of image data (bytes)
            documents: Optional list of (filename, data) tuples

        Yields:
            StreamChunk objects with response content

        Raises:
            ValueError: If model doesn't support attachments
        """
        # Get current model config
        model_config = self.get_current_model_config()
        provider = self._create_provider(model_config)

        # Validate capability gating
        if images and not provider.supports_feature("images"):
            logger.warning(f"Model {model_config.name} does not support images")
            raise ValueError(
                f"Model {model_config.name} does not support images. "
                "Please select a vision-capable model."
            )

        if documents and not provider.supports_feature("documents"):
            logger.warning(f"Model {model_config.name} does not support documents")
            raise ValueError(
                f"Model {model_config.name} does not support documents. "
                "Please select a model that supports document inputs."
            )

        # Add user message to history with attachments
        self.add_message("user", user_message, images, documents)

        # Build messages with agent context (includes system prompt and knowledge)
        messages_to_send = await self._build_messages_with_agent(user_message)

        logger.info(
            f"Streaming response from {model_config.name} "
            f"with agent '{self.current_agent_key}' "
            f"(conversation length: {len(self.messages)})"
        )

        # Stream response
        assistant_message = ""
        assistant_reasoning = ""
        try:
            async for chunk in provider.stream_chat(
                messages_to_send,
                max_tokens=model_config.max_tokens,
                temperature=model_config.temperature,
            ):
                # Accumulate assistant message and reasoning
                if chunk.content:
                    assistant_message += chunk.content
                if chunk.reasoning:
                    assistant_reasoning += chunk.reasoning

                yield chunk

            # Add complete assistant message to history (with reasoning for persistence)
            if assistant_message:
                self.add_message(
                    "assistant",
                    assistant_message,
                    reasoning=assistant_reasoning if assistant_reasoning else None,
                )

        except Exception as e:
            logger.error(f"Error during streaming: {e}", exc_info=True)
            # Don't add failed response to history
            raise

    @property
    def message_count(self) -> int:
        """Get number of messages in conversation."""
        return len(self.messages)

    def get_history(self) -> list[Message]:
        """
        Get conversation history.

        Returns:
            List of Message objects
        """
        return self.messages.copy()
