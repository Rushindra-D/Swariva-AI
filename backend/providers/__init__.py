"""
SWARIVA AI — Reasoning Providers Package
Provides factory initialization and unified access to LLM reasoning providers.
"""
import os
import logging
from typing import Tuple

from config import (
    EVON_BASE_URL,
    EVON_MODEL,
    EVON_TIMEOUT_SECONDS,
    GNANI_EVON_API_KEY,
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
)
from providers.base import BaseLLMProvider
from providers.knowledge_companion import KnowledgeCompanionProvider
from providers.evon_provider import EvonLLMProvider
from providers.groq_provider import GroqLLMProvider

logger = logging.getLogger("swariva.providers")


def get_llm_provider() -> Tuple[BaseLLMProvider, BaseLLMProvider]:
    """
    Returns (primary_provider, fallback_provider) based on current environment configuration.
    Guarantees that KnowledgeCompanionProvider is always available as fallback.
    """
    fallback_provider = KnowledgeCompanionProvider()

    # Tier 1: Check if Evon is explicitly pointed to an active hosted/cloud endpoint
    evon_url = os.getenv("EVON_BASE_URL", EVON_BASE_URL)
    evon_key = os.getenv("GNANI_EVON_API_KEY", GNANI_EVON_API_KEY)
    enable_evon = os.getenv("ENABLE_EVON", "false").lower() in ("true", "1", "yes")

    if enable_evon or (evon_url and "localhost" not in evon_url and "127.0.0.1" not in evon_url):
        logger.info("Initializing Tier 1: Gnani Evon v3.3 Provider at %s", evon_url)
        primary = EvonLLMProvider(
            base_url=evon_url,
            model=os.getenv("EVON_MODEL", EVON_MODEL),
            api_key=evon_key,
            timeout=EVON_TIMEOUT_SECONDS,
        )
        return primary, fallback_provider

    # Tier 2: Check if Groq / Cloud LLM API key is present
    cloud_key = os.getenv("LLM_API_KEY", LLM_API_KEY)
    cloud_url = os.getenv("LLM_BASE_URL", LLM_BASE_URL)
    cloud_model = os.getenv("LLM_MODEL", LLM_MODEL)

    if cloud_key and not cloud_key.startswith("placeholder") and not cloud_key.startswith("your_"):
        logger.info("Initializing Tier 2: Cloud LLM Provider (%s)", cloud_model)
        primary = GroqLLMProvider(
            api_key=cloud_key,
            base_url=cloud_url,
            model=cloud_model,
        )
        return primary, fallback_provider

    # Tier 3: Built-in Knowledge Companion Engine (100% offline, zero credit, instant)
    logger.info("Initializing Tier 3: Knowledge Companion Provider (Zero external cost).")
    return fallback_provider, fallback_provider


__all__ = [
    "BaseLLMProvider",
    "KnowledgeCompanionProvider",
    "EvonLLMProvider",
    "GroqLLMProvider",
    "get_llm_provider",
]
