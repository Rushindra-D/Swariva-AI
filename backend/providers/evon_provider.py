"""
SWARIVA AI — Gnani Evon v3.3 Reasoning Provider (Tier 1)

Integrates with Gnani Evon v3.3 (30B-A3B) via OpenAI-compatible endpoints
(such as hosted Gnani Evon, vLLM, SGLang, or llama.cpp server).
"""
import logging
from typing import List, Dict, Any, Optional
import httpx

from providers.base import BaseLLMProvider

logger = logging.getLogger("swariva.providers.evon")


class EvonLLMProvider(BaseLLMProvider):
    """
    Reasoning engine provider for Gnani Evon v3.3 (30B-A3B).
    Connects to any standard OpenAI-compatible server hosting Evon.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:30000/v1",
        model: str = "gnani/gnani-evon-v3.3-30B-A3B",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key or ""
        self.timeout = timeout
        self.name = f"gnani_evon:{model}"

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
                "Incorporate the real-time data naturally into your spoken response.\n"
            )

        prompt_with_context += (
            "\nREMINDER: Give a direct, spoken answer. "
            "Never repeat the user's question. Never say 'How can I help you?'. "
            "Keep the response concise (2-4 natural sentences) without markdown."
        )

        formatted_messages = [{"role": "system", "content": prompt_with_context}]
        formatted_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": 0.6,
            "max_tokens": 300,
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        logger.info("Calling Gnani Evon at %s/chat/completions (model=%s)", self.base_url, self.model)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
