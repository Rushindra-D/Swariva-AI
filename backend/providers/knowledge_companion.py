"""
SWARIVA AI — Knowledge Companion Provider (Tier 3)

Provides zero-latency, zero-external-cost, offline-resilient reasoning in
English, Telugu, and Hindi for festivals, technology, health boundaries,
accessibility, reminders, and daily companion dialogue.
"""
import logging
from typing import List, Dict, Any, Optional

from providers.base import BaseLLMProvider
from intent_classifier import IntentClassifier, IntentType
from knowledge_base import KnowledgeCompanionEngine

logger = logging.getLogger("swariva.providers.knowledge")


class KnowledgeCompanionProvider(BaseLLMProvider):
    """
    Intelligent built-in companion and reasoning engine for SWARIVA AI.
    100% offline-capable, guaranteeing zero echo and zero generic fallback.
    """

    def __init__(self):
        self.name = "knowledge_companion"

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        target_language: str,
        active_subject: Optional[str] = None,
        rag_context: Optional[str] = None,
    ) -> str:
        # If RAG context is provided (e.g., live weather or gold price retrieved by tool),
        # return the grounded fact directly formatted for speech.
        if rag_context:
            return rag_context.strip()

        if not messages:
            return self._default_greeting(target_language)

        last_user_msg = messages[-1]["content"].strip()
        history_dicts = messages[:-1]

        # 1. Semantic intent classification
        intent, entities = IntentClassifier.classify(
            query=last_user_msg,
            history=history_dicts,
            active_subject=active_subject,
        )

        # 2. Knowledge retrieval and direct answer generation
        response = KnowledgeCompanionEngine.get_response(
            intent=intent,
            entities=entities,
            language=target_language,
            history=history_dicts,
            active_subject=active_subject,
        )

        return response

    def _default_greeting(self, language: str) -> str:
        lang = language.lower()
        if "te" in lang:
            return "నమస్కారం! నేను స్వరివ. ఈరోజు మీతో మాట్లాడటం చాలా సంతోషంగా ఉంది."
        elif "hi" in lang:
            return "नमस्ते! मैं स्वरिवा हूँ। आज आपसे बातचीत करके मुझे बहुत खुशी हो रही है।"
        return "Hello! I am Swariva. It is wonderful to speak with you today."

