"""
SWARIVA AI — AI Reasoning Engine and Agent Module

Implements a modular AI companion with support for:
- Empathetic and accessible assistant personality
- Multilingual responses (English, Telugu, Hindi)
- Contextual memory and follow-up understanding
- Modular LLM provider architecture (Rule-based companion fallback + External API hook)
- Speech-ready text formatting (cleans markdown before Timbre TTS)
"""
import re
import os
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import httpx

from config import SUPPORTED_LANGUAGES
from conversation import ConversationSession

logger = logging.getLogger("swariva.agent")


# ── System Prompt & Core Directives ──
SYSTEM_PROMPT = """You are SWARIVA AI — "A voice that understands you."
You are an empathetic, intelligent, and highly accessible voice-first companion designed primarily for:
- People with visual impairments
- Elderly individuals needing daily companionship and reminders
- People with limited mobility seeking effortless voice navigation
- Anyone seeking an intelligent, caring multilingual voice companion

Core Directives:
1. Tone: Warm, respectful, patient, encouraging, and clear.
2. Conciseness: Speak clearly in 2-3 sentences where possible so that audio playback remains natural and fatigue-free.
3. Multilingual: Fluently converse in English, Telugu, and Hindi. Match the user's spoken language.
4. Boundaries: You are an AI companion, NOT a certified doctor, lawyer, or emergency service. If health or danger is mentioned, gently remind the user to contact their doctor, family, or emergency helpline.
5. Honesty: If you do not know something, acknowledge it honestly without fabricating answers.
"""


def clean_text_for_speech(text: str) -> str:
    """
    Strips markdown symbols, emojis, and formatting artifacts so that
    Gnani Timbre synthesizes natural, smooth spoken audio.
    """
    # Remove markdown bold/italics
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    cleaned = re.sub(r"\*([^*]+)\*", r"\1", text)
    cleaned = re.sub(r"__([^_]+)__", r"\1", text)
    cleaned = re.sub(r"_([^_]+)_", r"\1", text)
    # Remove markdown headers and list markers
    cleaned = re.sub(r"^#+\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^[*-]\s+", "", cleaned, flags=re.MULTILINE)
    # Remove URLs
    cleaned = re.sub(r"https?://\S+", "", cleaned)
    # Replace multiple spaces/newlines
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


@dataclass
class AgentReply:
    text: str
    speech_text: str
    language: str
    provider: str
    metadata: Dict[str, Any]


class BaseLLMProvider(ABC):
    """Abstract interface for modular reasoning providers."""

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        target_language: str,
    ) -> str:
        """Generate response text given conversation history and system instructions."""
        pass


class RuleBasedCompanionProvider(BaseLLMProvider):
    """
    Intelligent built-in companion engine tailored for SWARIVA AI.
    Provides immediate, zero-latency, zero-credit companion interaction in
    English, Hindi, and Telugu for everyday assistance, reminders, and companionship.
    """

    def __init__(self):
        self.name = "rule_based_companion"

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        target_language: str,
    ) -> str:
        if not messages:
            return self._default_greeting(target_language)

        last_user_msg = messages[-1]["content"].lower().strip()
        history_context = " ".join([m["content"].lower() for m in messages[:-1]])

        # Language-specific responses
        lang = target_language.lower()
        if "te" in lang or "telugu" in lang:
            return self._handle_telugu(last_user_msg, history_context)
        elif "hi" in lang or "hindi" in lang:
            return self._handle_hindi(last_user_msg, history_context)
        else:
            return self._handle_english(last_user_msg, history_context)

    def _default_greeting(self, language: str) -> str:
        if "te" in language:
            return "నమస్కారం! నేను స్వరివ. మీకు ఈరోజు ఎలా సహాయం చేయగలను?"
        elif "hi" in language:
            return "नमस्ते! मैं स्वरिवा हूँ। आज मैं आपकी क्या सहायता कर सकती हूँ?"
        return "Hello! I am Swariva, your intelligent voice assistant. How can I help you today?"

    def _handle_english(self, query: str, context: str) -> str:
        # Greetings
        if any(w in query for w in ["hello", "hi", "hey", "good morning", "good evening", "namaste"]):
            return "Hello! I'm Swariva, your voice companion. I am right here with you. How are you feeling today?"

        # Identity
        if any(w in query for w in ["who are you", "your name", "what are you", "what can you do"]):
            return (
                "I am Swariva AI, your multilingual voice companion. I'm designed to assist you with "
                "conversations, daily reminders, reading text aloud, and keeping you company in English, Hindi, and Telugu."
            )

        # Loneliness / Emotional support
        if any(w in query for w in ["lonely", "alone", "sad", "unhappy", "bored", "nobody to talk to"]):
            return (
                "I'm here with you. You're never completely alone. Would you like to talk about your day, "
                "listen to a comforting thought, or would you like me to note down something for you?"
            )

        # Health / Medical inquiry
        if any(w in query for w in ["doctor", "chest pain", "heart attack", "emergency", "medicine dose", "pain"]):
            return (
                "Please remember that I am an AI companion and cannot provide medical advice. "
                "If you are feeling unwell or have severe symptoms, please contact your doctor or trusted family member immediately."
            )

        # Reminders
        if any(w in query for w in ["remind", "reminder", "alarm", "medicine", "pill", "appointment"]):
            return (
                "I would be glad to help you keep track of your reminders! In our full dashboard, "
                "you can schedule medicine reminders and appointments with voice alerts."
            )

        # Accessibility / Vision
        if any(w in query for w in ["blind", "visually impaired", "can't see", "eyesight", "large text"]):
            return (
                "SWARIVA AI is built specially with high-contrast accessibility and full voice navigation. "
                "You can speak every command and I will speak back to you clearly."
            )

        # Thank you / Farewell
        if any(w in query for w in ["thank you", "thanks", "bye", "goodbye", "good night"]):
            return "You're very welcome! Take good care of yourself, and I am always here whenever you need me."

        # Follow-up context handling
        if any(w in query for w in ["yes", "tell me more", "what else", "continue"]):
            if "reminder" in context:
                return "You can say: 'Remind me to take my blood pressure medicine at 8 PM', and I will keep it ready for you."
            return "I am listening closely. Feel free to ask me anything or share what's on your mind."

        # General helpful companion response
        return (
            f"I hear you. You mentioned: '{query}'. As your voice companion, I'm here to support you. "
            "How would you like to proceed?"
        )

    def _handle_hindi(self, query: str, context: str) -> str:
        # Greetings
        if any(w in query for w in ["नमस्ते", "हेलो", "हाय", "प्रणाम", "सुप्रभात"]):
            return "नमस्ते! मैं स्वरिवा हूँ, आपकी आवाज सहायक। आज आप कैसा महसूस कर रहे हैं?"

        # Identity
        if any(w in query for w in ["तुम कौन हो", "आपका नाम", "क्या कर सकती हो"]):
            return (
                "मैं स्वरिवा एआई हूँ, आपकी बहुभाषी आवाज साथी। मैं आपसे बातचीत कर सकती हूँ, "
                "दवाइयों और महत्वपूर्ण कार्यों के रिमाइंडर रख सकती हूँ, और आपके साथ हिंदी, तेलुगु और अंग्रेजी में बात कर सकती हूँ।"
            )

        # Reminders
        if any(w in query for w in ["दवा", "याद दिलाओ", "रिमाइंडर", "गोली", "डॉक्टर"]):
            return (
                "मैं आपकी दवाइयों और जरूरी कामों की याद दिलाने में मदद कर सकती हूँ। "
                "आप मुझे समय और काम बता सकते हैं, मैं समय पर आपको याद दिलाऊँगी।"
            )

        # Emotional support
        if any(w in query for w in ["अकेला", "उदास", "मन नहीं लग रहा", "बोरे"]):
            return (
                "आप बिल्कुल अकेले नहीं हैं, मैं हमेशा आपके साथ हूँ। "
                "क्या आप अपने दिन के बारे में कुछ बताना चाहेंगे?"
            )

        # Health disclaimer
        if any(w in query for w in ["तबीयत खराब", "दर्द", "इमरजेंसी", "अस्पताल"]):
            return (
                "कृपया ध्यान दें कि मैं केवल एक एआई सहायक हूँ और डॉक्टर की जगह नहीं ले सकती। "
                "यदि आप अस्वस्थ महसूस कर रहे हैं, तो तुरंत अपने चिकित्सक या परिवार के सदस्य से संपर्क करें।"
            )

        # Gratitude
        if any(w in query for w in ["धन्यवाद", "शुक्रिया", "अलविदा", "बाय"]):
            return "आपका बहुत-बहुत धन्यवाद! अपना ख्याल रखें, मैं हमेशा आपकी मदद के लिए यहीं हूँ।"

        return f"मैंने आपकी बात सुनी: '{query}'। मैं आपकी किस प्रकार और सहायता करूँ?"

    def _handle_telugu(self, query: str, context: str) -> str:
        # Greetings
        if any(w in query for w in ["నమస్కారం", "హలో", "బాగున్నారా", "నమస్తే"]):
            return "నమస్కారం! నేను స్వరివ. ఈరోజు మీరు ఎలా ఉన్నారు? నేను మీకు ఎలా సహాయపడగలను?"

        # Identity
        if any(w in query for w in ["ఎవరు నువ్వు", "నీ పేరు", "ఏమి చేయగలవు"]):
            return (
                "నేను స్వరివ AI. దృష్టి లోపం ఉన్నవారు, వృద్ధులు మరియు రోజువారీ సహాయం కోరుకునే వారి కోసం రూపొందించిన వాయిస్ అసిస్టెంట్. "
                "నేను తెలుగు, హిందీ మరియు ఆంగ్లంలో మీతో మాట్లాడగలను."
            )

        # Reminders
        if any(w in query for w in ["మందులు", "గుర్తు చేయి", "రిమైండర్", "సమయం"]):
            return (
                "మీ మందులు మరియు ముఖ్యమైన పనుల రిమైండర్లను నేను గుర్తుంచుకుంటాను. "
                "మీకు ఏ సమయానికి ఏ పని గుర్తుచేయాలో నాకు చెప్పండి."
            )

        # Emotional support
        if any(w in query for w in ["ఒంటరిగా", "బాధగా", "బోర్"]):
            return (
                "మీరు ఒంటరిగా లేరు, నేను మీతోనే ఉన్నాను. "
                "మీ రోజు ఎలా గడిచిందో నాతో పంచుకోవాలనుకుంటున్నారా?"
            )

        # Health disclaimer
        if any(w in query for w in ["డాక్టర్", "నొప్పి", "అనారోగ్యం", "హాస్పిటల్"]):
            return (
                "దయచేసి గమనించండి: నేను ఒక AI సహాయకురాలిని మాత్రమే, డాక్టర్ని కాదు. "
                "మీకు ఆరోగ్యం బాగోలేకపోతే దయచేసి వెంటనే మీ వైద్యుడిని సంప్రదించండి."
            )

        # Gratitude
        if any(w in query for w in ["ధన్యవాదాలు", "థాంక్స్", "బై", "వెళ్ళొస్తా"]):
            return "చాలా ధన్యవాదాలు! జాగ్రత్తగా ఉండండి, మీకు ఎప్పుడు అవసరమైనా నేను ఇక్కడే ఉంటాను."

        return f"మీరు చెప్పింది విన్నాను: '{query}'. నేను మీకు ఎలా సహాయపడగలను?"


class ExternalLLMProvider(BaseLLMProvider):
    """
    Connects to an external OpenAI-compatible or hosted reasoning API
    (e.g., Groq, OpenRouter, Together AI, or a custom Gnani Evon vLLM host).
    Configurable entirely via environment variables.
    """

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.name = f"external_llm:{model}"

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        target_language: str,
    ) -> str:
        prompt_with_lang = f"{system_prompt}\nTarget response language: {target_language}."
        formatted_messages = [{"role": "system", "content": prompt_with_lang}]
        formatted_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": 0.7,
            "max_tokens": 250,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()


class SWARIVAAgent:
    """
    Coordinator agent for SWARIVA AI.
    Routes queries to the active LLM provider, manages context, and formats
    responses for text and speech.
    """

    def __init__(self):
        # Determine provider from environment
        external_key = os.getenv("LLM_API_KEY", "")
        external_url = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
        external_model = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

        self.fallback_provider = RuleBasedCompanionProvider()

        if external_key and not external_key.startswith("placeholder"):
            self.primary_provider: BaseLLMProvider = ExternalLLMProvider(
                api_key=external_key,
                base_url=external_url,
                model=external_model,
            )
            logger.info("Using External LLM provider: %s", external_model)
        else:
            self.primary_provider = self.fallback_provider
            logger.info("Using built-in RuleBasedCompanionProvider (zero external cost).")

    def _resolve_language(self, user_text: str, session: ConversationSession, requested_lang: str) -> str:
        """Determines the appropriate output language."""
        if requested_lang and requested_lang != "auto":
            return requested_lang
        if session.preferred_language and session.preferred_language != "auto":
            return session.preferred_language

        # Simple script detection for auto mode
        # Telugu Unicode range: 0x0C00 - 0x0C7F
        if any('\u0C00' <= char <= '\u0C7F' for char in user_text):
            return "telugu"
        # Devanagari (Hindi) range: 0x0900 - 0x097F
        if any('\u0900' <= char <= '\u097F' for char in user_text):
            return "hindi"

        return "english"

    async def generate_response(
        self,
        user_message: str,
        session: ConversationSession,
        language: str = "auto",
    ) -> AgentReply:
        """
        Processes a user message, maintains session context, and generates
        both display text and speech-optimized text.
        """
        # Determine language
        resolved_lang = self._resolve_language(user_message, session, language)

        # Add user message to session context
        session.add_user_message(user_message, language=resolved_lang)

        # Get recent context for reasoning
        history = session.get_history_for_llm(max_turns=6)

        # Attempt generation with primary provider, fall back gracefully
        reply_text = ""
        provider_used = "rule_based"

        try:
            reply_text = await self.primary_provider.generate(
                messages=history,
                system_prompt=SYSTEM_PROMPT,
                target_language=resolved_lang,
            )
            provider_used = getattr(self.primary_provider, "name", "primary")
        except Exception as e:
            logger.warning("Primary reasoning provider failed (%s). Falling back to built-in companion.", e)
            reply_text = await self.fallback_provider.generate(
                messages=history,
                system_prompt=SYSTEM_PROMPT,
                target_language=resolved_lang,
            )
            provider_used = "rule_based_fallback"

        # Record assistant reply in session
        session.add_assistant_message(reply_text, language=resolved_lang)

        # Clean response for natural voice synthesis via Gnani Timbre
        speech_text = clean_text_for_speech(reply_text)

        return AgentReply(
            text=reply_text,
            speech_text=speech_text,
            language=resolved_lang,
            provider=provider_used,
            metadata={
                "session_id": session.session_id,
                "history_length": len(session.messages),
                "resolved_language": resolved_lang,
            },
        )


# Global singleton instance for application use
agent = SWARIVAAgent()
