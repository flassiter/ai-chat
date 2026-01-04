"""Service for fetching, caching, and injecting agent knowledge."""

import html
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx

from ai_chat.config.models import AgentConfig, KnowledgeSource

logger = logging.getLogger(__name__)


@dataclass
class CachedKnowledge:
    """Cached knowledge content."""

    source_name: str
    url: str
    content: str
    fetched_at: datetime
    expires_at: datetime


class KnowledgeService:
    """Service for managing agent knowledge sources."""

    def __init__(self, cache_directory: str = "./data/knowledge_cache"):
        """
        Initialize knowledge service.

        Args:
            cache_directory: Directory for caching fetched content
        """
        self.cache_dir = Path(cache_directory).expanduser().resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache for active session
        self._memory_cache: dict[str, CachedKnowledge] = {}

        logger.info(f"KnowledgeService initialized: {self.cache_dir}")

    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL."""
        import hashlib

        return hashlib.sha256(url.encode()).hexdigest()[:16]

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get path to cached content file."""
        return self.cache_dir / f"{cache_key}.json"

    def check_relevance(
        self,
        user_message: str,
        knowledge_source: KnowledgeSource,
    ) -> tuple[bool, float]:
        """
        Check if a knowledge source is relevant to the user message.

        Uses keyword matching and topic detection without embeddings.

        Args:
            user_message: The user's message
            knowledge_source: Knowledge source to check

        Returns:
            Tuple of (is_relevant, confidence_score)
        """
        message_lower = user_message.lower()
        message_words = set(re.findall(r"\b\w+\b", message_lower))

        score = 0.0
        max_possible = 0.0

        # Check exact keyword matches (highest weight)
        for keyword in knowledge_source.keywords:
            max_possible += 1.0
            keyword_lower = keyword.lower()
            if keyword_lower in message_lower:
                score += 1.0
            elif any(word in keyword_lower for word in message_words):
                score += 0.5

        # Check topic matches (medium weight)
        for topic in knowledge_source.topics:
            max_possible += 0.5
            topic_lower = topic.lower()
            if topic_lower in message_lower:
                score += 0.5
            elif topic_lower in message_words:
                score += 0.3

        # Normalize score
        if max_possible > 0:
            confidence = score / max_possible
        else:
            confidence = 0.0

        # Threshold for relevance
        is_relevant = confidence >= 0.3

        logger.debug(
            f"Relevance check for '{knowledge_source.name}': "
            f"score={score:.2f}, confidence={confidence:.2f}, relevant={is_relevant}"
        )

        return is_relevant, confidence

    def get_relevant_sources(
        self,
        user_message: str,
        agent_config: AgentConfig,
    ) -> list[tuple[KnowledgeSource, float]]:
        """
        Get knowledge sources relevant to the user message.

        Args:
            user_message: User's message
            agent_config: Agent configuration

        Returns:
            List of (source, confidence) tuples, sorted by confidence
        """
        relevant = []

        for source in agent_config.knowledge_sources:
            is_relevant, confidence = self.check_relevance(user_message, source)
            if is_relevant:
                relevant.append((source, confidence))

        # Sort by confidence (highest first)
        relevant.sort(key=lambda x: x[1], reverse=True)

        return relevant

    async def fetch_knowledge(
        self,
        source: KnowledgeSource,
        force_refresh: bool = False,
    ) -> Optional[str]:
        """
        Fetch knowledge from a source URL.

        Implements caching with TTL support.

        Args:
            source: Knowledge source to fetch
            force_refresh: Bypass cache and fetch fresh

        Returns:
            Content string, or None if fetch failed
        """
        cache_key = self._get_cache_key(source.url)

        # Check memory cache first
        if not force_refresh and cache_key in self._memory_cache:
            cached = self._memory_cache[cache_key]
            if datetime.now() < cached.expires_at:
                logger.debug(f"Memory cache hit for: {source.name}")
                return cached.content

        # Check disk cache
        cache_path = self._get_cache_path(cache_key)
        if not force_refresh and cache_path.exists():
            try:
                with open(cache_path, "r") as f:
                    data = json.load(f)
                expires_at = datetime.fromisoformat(data["expires_at"])
                if datetime.now() < expires_at:
                    logger.debug(f"Disk cache hit for: {source.name}")
                    # Update memory cache
                    self._memory_cache[cache_key] = CachedKnowledge(
                        source_name=source.name,
                        url=source.url,
                        content=data["content"],
                        fetched_at=datetime.fromisoformat(data["fetched_at"]),
                        expires_at=expires_at,
                    )
                    return data["content"]
            except Exception as e:
                logger.warning(f"Failed to read cache for {source.name}: {e}")

        # Fetch from URL using context manager to ensure proper cleanup
        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                headers={"User-Agent": "AI-Chat-Knowledge-Fetcher/1.0"},
                follow_redirects=True,
            ) as client:
                response = await client.get(source.url)

                if response.status_code != 200:
                    logger.error(
                        f"Failed to fetch {source.name}: HTTP {response.status_code}"
                    )
                    return None

                content = response.text

            # Extract text from HTML (basic extraction)
            content = self._extract_text_from_html(content)

            # Truncate if too long (avoid context overflow)
            max_length = 50000  # ~12k tokens
            if len(content) > max_length:
                content = content[:max_length] + "\n\n[Content truncated...]"

            logger.info(f"Fetched knowledge from {source.name} ({len(content)} chars)")

        except httpx.TimeoutException:
            logger.error(f"Timeout fetching {source.name}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {source.name}: {e}")
            return None

        # Cache result
        now = datetime.now()
        expires_at = now + timedelta(hours=source.cache_ttl_hours)

        cached = CachedKnowledge(
            source_name=source.name,
            url=source.url,
            content=content,
            fetched_at=now,
            expires_at=expires_at,
        )

        self._memory_cache[cache_key] = cached

        # Persist to disk
        try:
            with open(cache_path, "w") as f:
                json.dump(
                    {
                        "source_name": source.name,
                        "url": source.url,
                        "content": content,
                        "fetched_at": now.isoformat(),
                        "expires_at": expires_at.isoformat(),
                    },
                    f,
                )
            logger.debug(f"Cached {source.name} to disk")
        except Exception as e:
            logger.warning(f"Failed to cache {source.name} to disk: {e}")

        return content

    def _extract_text_from_html(self, html_content: str) -> str:
        """
        Extract readable text from HTML.

        Uses basic regex extraction. For production, consider
        beautifulsoup4 or readability-lxml.
        """
        # Remove script and style elements
        text = re.sub(r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)

        # Decode HTML entities
        text = html.unescape(text)

        # Clean up whitespace
        text = re.sub(r"\s+", " ", text)
        text = text.strip()

        return text

    async def fetch_relevant_knowledge(
        self,
        user_message: str,
        agent_config: AgentConfig,
        max_sources: int = 3,
    ) -> list[tuple[str, str]]:
        """
        Fetch relevant knowledge for a user message.

        Args:
            user_message: User's message
            agent_config: Agent configuration
            max_sources: Maximum sources to fetch

        Returns:
            List of (source_name, content) tuples
        """
        relevant_sources = self.get_relevant_sources(user_message, agent_config)

        if not relevant_sources:
            return []

        # Limit number of sources
        sources_to_fetch = relevant_sources[:max_sources]

        # Fetch all relevant sources
        results = []
        for source, _ in sources_to_fetch:
            content = await self.fetch_knowledge(source)
            if content:
                results.append((source.name, content))

        return results
