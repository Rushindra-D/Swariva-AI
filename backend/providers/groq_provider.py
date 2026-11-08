"""
SWARIVA AI — High-Speed Cloud Reasoning Provider (Tier 2)

Connects to Groq Cloud (or compatible ultra-fast inference APIs) for sub-second,
natural conversational reasoning in English, Hindi, and Telugu.
"""
import logging
from typing import List, Dict, Any, Optional
import httpx

from providers.base import BaseLLMProvider

logger = logging.getLogger("swariva.providers.groq")


class GroqLLMProvider(BaseLLMProvider):
    """
    High-speed cloud LLM provider using Groq or any OpenAI-compatible API.
    Offers ~150-300ms latency, ideal for voice-first interactions.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.groq.com/openai/v1",
        model: str = "llama-3.1-8b-instant",
        timeout: float = 20.0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.name = f"cloud_llm:{model}"

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        target_language: str,
        active_subject: Optional[str] = None,
        rag_context: Optional[str] = None,
    ) -> str:
        prompt_with_context = (
            f"{system_prompt}\n\n"
            f"TARGET RESPONSE LANGUAGE: {target_language.upper()}.\n"
            f"CONVERSATIONAL CONTEXT SUBJECT: {active_subject or 'General'}.\n"
        )
        if rag_context:
            prompt_with_context += (
                f"\nVERIFIED REAL-TIME DATA (GROUND TRUTH):\n{rag_context}\n"
                "Incorporate the real-time data accurately into your spoken answer.\n"
            )

        prompt_with_context += (
            "\nREMINDER: Give a direct, spoken answer. "
            "Never repeat the user's question. Never say 'How can I help you?'. "
            "Keep the response concise (2-4 natural sentences) without markdown formatting."
        )

        formatted_messages = [{"role": "system", "content": prompt_with_context}]
        formatted_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": 0.6,
            "max_tokens": 300,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
