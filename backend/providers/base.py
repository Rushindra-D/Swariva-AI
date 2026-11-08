"""
SWARIVA AI — Base LLM Provider Interface
Defines the standard abstract interface for all reasoning and language model providers.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseLLMProvider(ABC):
    """Abstract interface for modular reasoning providers in SWARIVA AI."""

    name: str = "base"

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        target_language: str,
        active_subject: Optional[str] = None,
        rag_context: Optional[str] = None,
    ) -> str:
        """
        Generate response text given conversation history and system instructions.

        Args:
            messages: List of prior messages formatted as {"role": "user"|"assistant", "content": "..."}.
            system_prompt: The base companion persona directives and constraints.
            target_language: Desired output language ('english', 'telugu', 'hindi').
            active_subject: Current conversational subject/topic if known.
            rag_context: Real-time retrieved factual data (weather, gold price, reminders) to ground the answer.

        Returns:
            Spoken-friendly response string.
        """
        pass
