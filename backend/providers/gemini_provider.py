"""
SWARIVA AI — Google Gemini Reasoning Provider (Tier 1)

Integrates with the official Google Gen AI SDK (google-genai) for
intelligent, multilingual reasoning, general knowledge Q&A, and conversational voice interaction.
Supports conversation history, RAG grounding, and spoken-clean formatting.
"""
import time
import asyncio
import logging
from typing import List, Dict, Any, Optional

from providers.base import BaseLLMProvider

logger = logging.getLogger("swariva.providers.gemini")


class GeminiProviderError(Exception):
    """Base exception for Gemini provider errors."""
    pass


class GeminiAuthError(GeminiProviderError):
    """Raised when the Gemini API key is missing, invalid, or unauthorized."""
    pass


class GeminiQuotaError(GeminiProviderError):
    """Raised when the Gemini API rate limit or billing quota is exhausted."""
    pass


class GeminiModelError(GeminiProviderError):
    """Raised when the requested Gemini model is invalid or unavailable."""
    pass


class GeminiTimeoutError(GeminiProviderError):
    """Raised when the Gemini API request exceeds the configured timeout."""
    pass


class GeminiProvider(BaseLLMProvider):
    """
    Primary reasoning engine using Google Gemini.
    Generates intelligent, multilingual, speech-friendly responses
    for voice-first accessible companion interactions.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.5-flash-lite",
        timeout: float = 30.0,
    ):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiProvider.")

        self._api_key = api_key
        self.model = model
        self.timeout = timeout
        self.name = f"gemini:{model}"
        self.last_latency: float = 0.0

        # Lazy-initialize the client to avoid import-time overhead
        self._client = None

    def _get_client(self):
        """Lazily initialize the official Google GenAI client."""
        if self._client is None:
            from google import genai

            # Initialize client with default verified transport (urllib3/requests) for reliable SSL handshake
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        target_language: str,
        active_subject: Optional[str] = None,
        rag_context: Optional[str] = None,
    ) -> str:
        """
        Generates an intelligent response using Google Gemini.

        Args:
            messages: Conversation turns [{"role": "user"|"assistant", "content": "..."}].
            system_prompt: Base companion instructions and constraints.
            target_language: Desired output language ('english', 'telugu', 'hindi').
            active_subject: Current conversational subject/topic if known.
            rag_context: Real-time retrieved factual data (weather, gold price, reminders).

        Returns:
            Clean spoken response string.
        """
        start_time = time.time()

        # Build comprehensive system instructions with multilingual and accessibility rules
        system_instruction = (
            f"{system_prompt}\n\n"
            f"=== TARGET LANGUAGE DIRECTIVE ===\n"
            f"You MUST respond fluently in: {target_language.upper()}.\n"
            f"- If English: respond in natural, clear English.\n"
            f"- If Telugu: respond in authentic, natural Telugu script (తెలుగు).\n"
            f"- If Hindi: respond in authentic, natural Hindi Devanagari script (हिंदी).\n"
            f"- If the user code-mixes (e.g., Telugu-English or Hindi-English), respond in the requested language while keeping commonly understood technical loanwords.\n"
            f"- Do NOT unexpectedly change the language away from {target_language.upper()} unless the user explicitly requests another language.\n"
            f"- Do NOT translate proper nouns, brand names, or well-known technical terms unnecessarily.\n\n"
            f"=== CONVERSATIONAL CONTEXT ===\n"
            f"Active Subject/Topic: {active_subject or 'General conversation'}\n"
            f"Use the conversation history to understand pronouns (e.g., 'it', 'they', 'when is it', 'how does it work') "
            f"and follow-up questions seamlessly. If the user shifts to a completely new topic, transition smoothly to the new topic without lingering on the previous one.\n"
        )

        if rag_context:
            system_instruction += (
                f"\n=== VERIFIED REAL-TIME DATA (GROUND TRUTH) ===\n"
                f"{rag_context}\n"
                f"Incorporate this real-time data accurately and naturally into your response. Do not invent contradictory details.\n"
            )

        system_instruction += (
            "\n=== VOICE-FIRST ACCESSIBILITY RULES ===\n"
            "1. Answer directly and informatively. Give factual, well-reasoned answers to questions.\n"
            "2. NEVER repeat or echo the user's question before answering (e.g., do not say 'You asked about...', 'Regarding your question on...').\n"
            "3. NEVER use generic deflections like 'I am here with you' when asked a specific question.\n"
            "4. Keep answers concise, natural, and conversational (typically 2 to 4 spoken sentences) so audio playback is smooth for visually impaired or elderly users.\n"
            "5. NO markdown: do not use asterisks (**), bolding, bullet points, headers (#), or emoji, as these will be read aloud awkwardly by text-to-speech.\n"
            "6. Safety: Never claim to be a doctor or emergency service. For medical questions, offer general educational information and recommend consulting a healthcare professional.\n"
        )

        # Convert conversation messages into Google GenAI Content objects
        from google.genai import types

        contents: List[types.Content] = []
        for msg in messages:
            role = msg.get("role", "user")
            content_text = msg.get("content", "").strip()
            if not content_text:
                continue

            # Gemini uses "user" and "model" roles
            gemini_role = "model" if role in ("assistant", "model") else "user"
            contents.append(
                types.Content(
                    role=gemini_role,
                    parts=[types.Part.from_text(text=content_text)],
                )
            )

        # Ensure there is at least one message and that conversation ends with a user message
        if not contents or contents[-1].role != "user":
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text="Please respond to the latest request.")],
                )
            )

        logger.info(
            "Calling Gemini (model=%s, lang=%s, turns=%d)",
            self.model, target_language, len(contents),
        )

        try:
            client = self._get_client()

            # Execute generation via asyncio.to_thread with client.models.generate_content
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                    max_output_tokens=450,
                ),
            )

            self.last_latency = round(time.time() - start_time, 3)

            # Validate response
            if response and response.text:
                content = response.text.strip()
                if content:
                    logger.info(
                        "Gemini generated response in %.2fs (length=%d characters)",
                        self.last_latency, len(content),
                    )
                    return content

            # Handle empty response
            self.last_latency = round(time.time() - start_time, 3)
            logger.warning("Gemini returned an empty response.")
            raise GeminiProviderError("Gemini generated an empty response. Please try rephrasing your question.")

        except (GeminiAuthError, GeminiQuotaError, GeminiModelError, GeminiTimeoutError, GeminiProviderError):
            raise
        except ImportError:
            self.last_latency = round(time.time() - start_time, 3)
            logger.error("google-genai package is not installed.")
            raise GeminiProviderError("Google Gen AI SDK is not installed. Run: pip install google-genai")
        except Exception as e:
            self.last_latency = round(time.time() - start_time, 3)
            err_str = str(e)
            err_lower = err_str.lower()

            logger.error("Gemini API error (%s): %s", type(e).__name__, err_str)

            if any(k in err_lower for k in ["api_key", "api key", "401", "403", "unauthenticated", "permission_denied"]):
                raise GeminiAuthError(
                    "Invalid or unauthorized Gemini API key. Please check GEMINI_API_KEY in your .env file."
                ) from e
            elif any(k in err_lower for k in ["429", "quota", "rate limit", "resource_exhausted"]):
                raise GeminiQuotaError(
                    "Gemini API rate limit or quota exceeded. Please wait a moment before trying again."
                ) from e
            elif any(k in err_lower for k in ["not found", "model", "404"]) and "model" in err_lower:
                raise GeminiModelError(
                    f"Gemini model '{self.model}' is not available or unrecognized. Please check GEMINI_MODEL in .env."
                ) from e
            elif any(k in err_lower for k in ["timeout", "timed out", "deadline"]):
                raise GeminiTimeoutError(
                    f"Gemini request timed out after {self.timeout}s. Please check your internet connection."
                ) from e
            else:
                raise GeminiProviderError(
                    f"Gemini reasoning error: {err_str}"
                ) from e
