"""AWS Bedrock provider implementation."""

import logging
from typing import AsyncIterator, Optional

import boto3
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
    PartialCredentialsError,
)

from ai_chat.config.models import ModelConfig
from ai_chat.providers.base import (
    BaseProvider,
    Message,
    StreamChunk,
    AuthenticationError,
    ConnectionError,
    RateLimitError,
    ProviderError,
)

logger = logging.getLogger(__name__)


class BedrockProvider(BaseProvider):
    """AWS Bedrock provider using converse_stream API."""

    def __init__(self, config: ModelConfig):
        """
        Initialize Bedrock provider.

        Args:
            config: Model configuration

        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        if not config.model_id:
            raise ValueError(
                f"Bedrock provider requires 'model_id' field in config for {config.name}"
            )

        self.config = config
        self.model_id = config.model_id
        self.region = config.region or "us-east-1"

        # Initialize boto3 client
        try:
            self.client = boto3.client(
                "bedrock-runtime",
                region_name=self.region,
            )
            logger.info(
                f"Bedrock provider initialized: model={self.model_id}, region={self.region}"
            )
        except (NoCredentialsError, PartialCredentialsError) as e:
            logger.error(f"AWS credentials not found: {e}")
            raise AuthenticationError(
                f"AWS credentials not configured. Please run 'aws configure' or set AWS environment variables."
            ) from e
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            raise ProviderError(f"Failed to initialize Bedrock: {e}") from e

    async def stream_chat(
        self, messages: list[Message], max_tokens: int, temperature: float
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream chat completion from AWS Bedrock.

        Args:
            messages: Conversation history
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Yields:
            StreamChunk objects with response content

        Raises:
            AuthenticationError: If AWS credentials are invalid
            RateLimitError: If rate limited
            ConnectionError: If unable to connect
            ProviderError: For other errors
        """
        # Convert messages to Bedrock format
        bedrock_messages = self._convert_messages(messages)

        # Prepare request
        request = {
            "modelId": self.model_id,
            "messages": bedrock_messages,
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": temperature,
            },
        }

        logger.info(
            f"Starting Bedrock stream: model={self.model_id}, "
            f"messages={len(messages)}, max_tokens={max_tokens}"
        )
        logger.debug(f"Bedrock request: {request}")

        try:
            # Call converse_stream API
            response = self.client.converse_stream(**request)

            logger.debug("Bedrock stream response received")

            # Process stream events
            async for chunk in self._process_stream(response):
                yield chunk

            logger.info("Bedrock stream completed")

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            logger.error(f"Bedrock ClientError: {error_code} - {error_message}")

            # Handle specific error codes
            if error_code in ["UnrecognizedClientException", "InvalidSignatureException"]:
                raise AuthenticationError(
                    f"AWS authentication failed for {self.config.name}. "
                    f"Please check your credentials."
                ) from e
            elif error_code == "ThrottlingException":
                raise RateLimitError(
                    f"Rate limit exceeded for {self.config.name}. Please try again later."
                ) from e
            elif error_code in ["AccessDeniedException", "ResourceNotFoundException"]:
                raise AuthenticationError(
                    f"Access denied to model {self.model_id}. "
                    f"Please check model access in AWS Bedrock console."
                ) from e
            else:
                raise ProviderError(f"Bedrock error: {error_message}") from e

        except (BotoCoreError, ConnectionError) as e:
            logger.error(f"Bedrock connection error: {e}")
            raise ConnectionError(
                f"Cannot connect to AWS Bedrock in region {self.region}. "
                f"Please check your network connection."
            ) from e

        except Exception as e:
            logger.error(f"Unexpected Bedrock error: {e}", exc_info=True)
            raise ProviderError(f"Unexpected Bedrock error: {e}") from e

    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        """
        Convert internal Message format to Bedrock converse API format.

        Args:
            messages: Internal message list

        Returns:
            List of Bedrock-formatted message dicts
        """
        bedrock_messages = []

        for msg in messages:
            # Basic text content
            content = [{"text": msg.content}]

            # Add images if present
            if msg.images:
                for image_data in msg.images:
                    content.append(
                        {
                            "image": {
                                "format": "png",  # Could be detected from data
                                "source": {"bytes": image_data},
                            }
                        }
                    )

            # Add documents if present
            if msg.documents:
                for filename, doc_data in msg.documents:
                    # For now, add as text (could be enhanced with document extraction)
                    content.append({"text": f"[Document: {filename}]"})

            bedrock_messages.append(
                {
                    "role": msg.role,
                    "content": content,
                }
            )

        logger.debug(f"Converted {len(messages)} messages to Bedrock format")
        return bedrock_messages

    async def _process_stream(self, response) -> AsyncIterator[StreamChunk]:
        """
        Process Bedrock stream events.

        Args:
            response: Bedrock stream response

        Yields:
            StreamChunk objects
        """
        stream = response.get("stream")
        if not stream:
            logger.warning("No stream in Bedrock response")
            return

        # Track content block types to distinguish reasoning from regular content
        content_block_types = {}

        for event in stream:
            # Content block start - identifies block type
            if "contentBlockStart" in event:
                start = event["contentBlockStart"]
                content_block_index = start.get("contentBlockIndex", 0)

                # Check if this is a reasoning block
                if "start" in start:
                    start_data = start["start"]
                    # Bedrock uses "thinkingContent" or similar for reasoning
                    if "thinkingContent" in start_data or "reasoning" in str(start_data).lower():
                        content_block_types[content_block_index] = "reasoning"
                        logger.debug(f"Detected reasoning block at index {content_block_index}")
                    else:
                        content_block_types[content_block_index] = "text"

            # Content block delta - the main content chunks
            elif "contentBlockDelta" in event:
                delta = event["contentBlockDelta"]["delta"]
                content_block_index = event["contentBlockDelta"].get("contentBlockIndex", 0)

                # Determine if this is reasoning or regular content
                is_reasoning = content_block_types.get(content_block_index) == "reasoning"

                if "text" in delta:
                    text = delta["text"]
                    if is_reasoning:
                        logger.debug(f"Reasoning chunk: {text[:50]}...")
                        yield StreamChunk(reasoning=text, is_reasoning=True)
                    else:
                        yield StreamChunk(content=text)

            # Metadata - could contain stop reason
            elif "metadata" in event:
                metadata = event["metadata"]
                logger.debug(f"Bedrock metadata: {metadata}")

                # Check for stop reason
                if "stopReason" in metadata:
                    stop_reason = metadata["stopReason"]
                    logger.info(f"Bedrock stream stopped: {stop_reason}")
                    yield StreamChunk(done=True)

            # Message stop - end of stream
            elif "messageStop" in event:
                logger.debug("Bedrock message stop event")
                yield StreamChunk(done=True)

            # Errors in stream
            elif "error" in event:
                error = event["error"]
                logger.error(f"Bedrock stream error: {error}")
                raise ProviderError(f"Stream error: {error}")

            else:
                # Log unknown events for debugging
                logger.debug(f"Unknown Bedrock event: {list(event.keys())}")

    def supports_feature(self, feature: str) -> bool:
        """
        Check if provider supports a specific feature.

        Args:
            feature: Feature name ('images', 'documents', 'reasoning')

        Returns:
            True if feature is supported
        """
        # Claude models support images
        if feature == "images":
            return "claude" in self.model_id.lower()

        # Claude models support documents (via text extraction)
        if feature == "documents":
            return "claude" in self.model_id.lower()

        # Claude extended thinking models support reasoning
        if feature == "reasoning":
            return "extended" in self.model_id.lower() or "thinking" in self.model_id.lower()

        return False
