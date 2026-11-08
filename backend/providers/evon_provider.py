"""
SWARIVA AI — Gnani Evon v3.3 Reasoning Provider (Tier 1)

Integrates with Gnani Evon v3.3 (30B-A3B) via OpenAI-compatible endpoints
(such as hosted Gnani Evon, Hugging Face Inference Endpoints, vLLM, SGLang, or llama.cpp server).
Measures latency, enforces spoken-clean formatting, and supports real-time RAG context injection.
"""
import time
import logging
from typing import List, Dict, Any, Optional
import httpx

from providers.base import BaseLLMProvider

logger = logging.getLogger("swariva.providers.evon")


class EvonLLMProvider(BaseLLMProvider):
    """
    Reasoning engine provider for Gnani Evon v3.3 (30B-A3B).
    Connects to any standard OpenAI-compatible server hosting Evon or
    a Hugging Face Inference Endpoint.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:30000/v1",
        model: str = "gnani/gnani-evon-v3.3-30B-A3B",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        # If base_url does not end with /v1 and is an OpenAI compatible endpoint, keep as is
        self.model = model
        self.api_key = api_key or ""
        self.timeout = timeout
        self.name = f"gnani_evon:{model}"
        self.last_latency: float = 0.0

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        target_language: str,
        active_subject: Optional[str] = None,
        rag_context: Optional[str] = None,
    ) -> str:
        start_time = time.time()

        prompt_with_context = (
            f"{system_prompt}\n\n"
            f"TARGET RESPONSE LANGUAGE: {target_language.upper()}.\n"
            f"CONVERSATIONAL CONTEXT SUBJECT: {active_subject or 'General'}.\n"
        )
        if rag_context:
            prompt_with_context += (
                f"\nVERIFIED REAL-TIME DATA (GROUND TRUTH):\n{rag_context}\n"
                "Incorporate the real-time data accurately and naturally into your spoken response.\n"
            )

        prompt_with_context += (
            "\nREMINDER: Give a direct, spoken answer. "
            "Never repeat the user's question. Never say 'How can I help you?'. "
            "Respond in 2-4 clear spoken sentences without any markdown formatting."
        )

        formatted_messages = [{"role": "system", "content": prompt_with_context}]
        formatted_messages.extend(messages)

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": 0.6,
            "max_tokens": 300,
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        endpoint_url = f"{self.base_url}/chat/completions" if not self.base_url.endswith("/chat/completions") else self.base_url

        logger.info("Calling Gnani Evon at %s (model=%s, lang=%s)", endpoint_url, self.model, target_language)
        timeout_cfg = httpx.Timeout(self.timeout, connect=4.0)
        try:
            async with httpx.AsyncClient(timeout=timeout_cfg) as client:
                resp = await client.post(
                    endpoint_url,
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                self.last_latency = round(time.time() - start_time, 3)

                content = data["choices"][0]["message"]["content"].strip()
                logger.info("Evon response received in %.2fs (length=%d)", self.last_latency, len(content))
                return content
        except httpx.ConnectError as e:
            self.last_latency = round(time.time() - start_time, 3)
            logger.error("Evon connection failed: Cannot reach %s (%s)", endpoint_url, e)
            raise ConnectionError(f"Could not connect to Gnani Evon endpoint at {self.base_url}. Verify endpoint status.")
        except httpx.TimeoutException as e:
            self.last_latency = round(time.time() - start_time, 3)
            logger.error("Evon request timed out after %.1fs", self.timeout)
            raise TimeoutError(f"Gnani Evon request timed out after {self.timeout}s.")
        except Exception as e:
            self.last_latency = round(time.time() - start_time, 3)
            logger.error("Evon inference error: %s", e)
            raise
