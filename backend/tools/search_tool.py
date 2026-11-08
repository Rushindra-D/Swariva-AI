"""
SWARIVA AI — Live Web & Encyclopedic Search Tool
Fetches real-time facts and authoritative definitions via Wikipedia REST API
and DuckDuckGo Instant Answers. Used for RAG grounding on arbitrary queries.
"""
import re
import urllib.parse
import logging
from typing import Dict, Any, Optional
import httpx

from tools.base import BaseTool, ToolResult

logger = logging.getLogger("swariva.tools.search")


class SearchTool(BaseTool):
    """Tool for retrieving verified encyclopedic knowledge and web facts."""

    name = "search_tool"
    description = "Searches for real-time facts, encyclopedic definitions, and concepts."

    TRIGGER_WORDS = [
        "search for", "who is", "what is", "where is", "why is", "how does", "how is",
        "tell me about", "explain", "define", "meaning of",
        "వెతకండి", "ఎవరు", "ఏమిటి", "అంటే ఏమిటి", "ఎందుకు", "ఎలా", "వివరించండి",
        "सर्च करो", "कौन है", "क्या है", "क्यों", "कैसे", "समझाओ"
    ]

    def can_handle(self, query: str) -> bool:
        lower = query.lower()
        # Exclude weather, gold, and reminders which have dedicated specialized tools
        if any(w in lower for w in [
            "weather", "temperature", "climate", "forecast", "వాతావరణం", "मौसम",
            "gold", "silver", "price of", "rate of", "బంగారం", "వెండి", "सोना", "चाँदी", "चांदी",
            "remind", "reminder", "alarm", "schedule", "గుర్తు", "రిమైండర్", "याद दिलाओ"
        ]):
            return False

        # Exclude pure greetings
        if lower.strip() in [
            "hello", "hi", "hey", "good morning", "good evening", "namaste",
            "నమస్కారం", "హలో", "హాయ్", "బాగున్నారా", "नमस्ते", "हेलो", "प्रणाम"
        ]:
            return False

        # Handle any general informational query
        if any(term in lower for term in self.TRIGGER_WORDS):
            return True

        # Catch question formats with a question mark
        if "?" in query and len(query.split()) >= 2:
            return True

        return False

    def _extract_topic(self, query: str) -> str:
        """Extracts the core entity name from a question."""
        cleaned = re.sub(
            r"^(?:please\s+)?(?:what\s+is\s+(?:a\s+|an\s+|the\s+)?|who\s+is\s+(?:a\s+|an\s+|the\s+)?|where\s+is\s+(?:the\s+)?|why\s+is\s+(?:the\s+)?|why\s+do\s+|how\s+does\s+(?:a\s+|an\s+|the\s+)?|how\s+do\s+|explain\s+|tell\s+me\s+about\s+|search\s+for\s+|define\s+)",
            "", query.strip(), flags=re.IGNORECASE,
        )
        # Remove trailing question marks and punctuation
        cleaned = re.sub(r"[\?\.!]+$", "", cleaned).strip()
        # Clean Telugu and Hindi markers
        cleaned = re.sub(r"(?:అంటే\s+ఏమిటి|గురించి\s+చెప్పండి|గురించి\s+తెలుపండి|ఎవరు|ఎక్కడ|ఎందుకు|ఎలా|ఏమిటి)[\?\.!]?$", "", cleaned).strip()
        cleaned = re.sub(r"(?:क्या\s+होता\s+है|क्या\s+है|के\s+बारे\s+में\s+बताओ|कौन\s+है|कहाँ\s+है|कैसे\s+होता\s+है)[\?\.!]?$", "", cleaned).strip()
        return cleaned or query.strip()

    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> ToolResult:
        topic = self._extract_topic(query)
        clean_q = query.strip()
        headers = {"User-Agent": "SwarivaAI/1.0 (contact@swariva.ai)"}

        # 1. Try Wikipedia REST API first (authoritative and concise)
        if topic and len(topic) >= 2:
            encoded_topic = urllib.parse.quote(topic.replace(" ", "_"))
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_topic}"
            try:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    resp = await client.get(wiki_url, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        extract = data.get("extract", "").strip()
                        if extract and len(extract) > 20:
                            # Keep extract concise (first 2-3 sentences)
                            sentences = re.split(r"(?<=[.!?])\s+", extract)
                            spoken_en = " ".join(sentences[:3])

                            return ToolResult(
                                success=True,
                                tool_name=self.name,
                                data={"topic": topic, "extract": spoken_en, "url": data.get("content_urls", {}).get("desktop", {}).get("page")},
                                spoken_summary={
                                    "english": spoken_en,
                                    "telugu": f"{topic} గురించి: {spoken_en}",
                                    "hindi": f"{topic} के संदर्भ में: {spoken_en}",
                                },
                                source="Wikipedia Reference",
                            )
            except Exception as e:
                logger.info("Wikipedia lookup failed (%s), trying DuckDuckGo", e)

        # 2. Try DuckDuckGo Instant Answer as fallback
        url = "https://api.duckduckgo.com/"
        params = {
            "q": clean_q,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        }

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    abstract = data.get("AbstractText") or data.get("Answer")
                    if abstract:
                        sentences = re.split(r"(?<=[.!?])\s+", abstract)
                        spoken = " ".join(sentences[:3])
                        return ToolResult(
                            success=True,
                            tool_name=self.name,
                            data={"abstract": spoken, "source": data.get("AbstractSource", "Web")},
                            spoken_summary={"english": spoken, "telugu": spoken, "hindi": spoken},
                            source="DuckDuckGo Instant Answer",
                        )
        except Exception as e:
            logger.info("Search lookup timed out or failed (%s)", e)

        return ToolResult(
            success=False,
            tool_name=self.name,
            data={"query": clean_q},
            spoken_summary={
                "english": f"I checked for information on {clean_q}. Let me assist you further with this topic.",
                "telugu": f"{clean_q} గురించి వివరాలను పరిశీలించాను.",
                "hindi": f"{clean_q} के संबंध में जानकारी खोजी।",
            },
            source="Search Fallback",
        )
