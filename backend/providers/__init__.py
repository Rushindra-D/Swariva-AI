"""
SWARIVA AI — Reasoning Providers Package
Provides factory initialization and unified access to LLM reasoning providers.
"""
import logging
from typing import Tuple

from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_TIMEOUT_SECONDS,
)
from providers.base import BaseLLMProvider
from providers.knowledge_companion import KnowledgeCompanionProvider
from providers.gemini_provider import (
    GeminiProvider,
    GeminiProviderError,
    GeminiAuthError,
    GeminiQuotaError,
    GeminiModelError,
    GeminiTimeoutError,
)

logger = logging.getLogger("swariva.providers")


def get_llm_provider() -> Tuple[BaseLLMProvider, BaseLLMProvider]:
    """
    Returns (primary_provider, fallback_provider) based on current environment configuration.

    Priority:
      Tier 1: Google Gemini (if GEMINI_API_KEY is configured)
      Tier 2: KnowledgeCompanionProvider (offline, zero external cost, always available)
    """
    fallback_provider = KnowledgeCompanionProvider()

    # Tier 1: Google Gemini
    if GEMINI_API_KEY and not GEMINI_API_KEY.startswith("placeholder") and not GEMINI_API_KEY.startswith("your_"):
        logger.info("Initializing Tier 1: Google Gemini Provider (model=%s)", GEMINI_MODEL)
        try:
            primary = GeminiProvider(
                api_key=GEMINI_API_KEY,
                model=GEMINI_MODEL,
                timeout=GEMINI_TIMEOUT_SECONDS,
            )
            return primary, fallback_provider
        except Exception as e:
            logger.error("Failed to initialize Gemini provider: %s. Falling back.", e)

    # Tier 2: Built-in Knowledge Companion Engine (100% offline, zero credit, instant)
    logger.info("Initializing Tier 2: Knowledge Companion Provider (Zero external cost).")
    return fallback_provider, fallback_provider


__all__ = [
    "BaseLLMProvider",
    "KnowledgeCompanionProvider",
    "GeminiProvider",
    "GeminiProviderError",
    "GeminiAuthError",
    "GeminiQuotaError",
    "GeminiModelError",
    "GeminiTimeoutError",
    "get_llm_provider",
]
