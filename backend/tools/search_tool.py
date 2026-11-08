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
        "search for", "who is", "what is the capital", "population of", "latest news",
        "define", "tell me about",
        "వెతకండి", "ఎవరు", "రాజధాని",
        "सर्च करो", "कौन है", "राजधानी क्या है"
    ]

    def can_handle(self, query: str) -> bool:
        lower = query.lower()
        if any(term in lower for term in self.TRIGGER_WORDS):
            return True
        # Also trigger on general factual inquiry questions
        if re.search(r"^(?:what\s+is|who\s+is|explain|tell\s+me\s+about)\s+[\w\s]{3,40}\??$", lower):
            # Exclude weather, gold, reminder which have specialized tools
            if not any(w in lower for w in ["weather", "temperature", "gold", "price", "rate", "remind", "alarm"]):
                return True
        return False

    def _extract_topic(self, query: str) -> str:
        """Extracts the core entity name from a question."""
        cleaned = re.sub(
            r"^(?:please\s+)?(?:what\s+is\s+(?:a\s+|an\s+|the\s+)?|who\s+is\s+(?:a\s+|an\s+|the\s+)?|explain\s+|tell\s+me\s+about\s+|search\s+for\s+)",
            "", query.strip(), flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"\?+$", "", cleaned).strip()
        return cleaned

    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> ToolResult:
        topic = self._extract_topic(query)
        clean_q = query.strip()
        headers = {"User-Agent": "SwarivaAI/1.0 (contact@swariva.ai)"}

        # 1. Try Wikipedia REST API first (authoritative and concise)
        if topic:
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
                                    "telugu": f"{topic} గురించి వివరాలు: {spoken_en}",
                                    "hindi": f"{topic} के बारे में: {spoken_en}",
                                },
                                source="Wikipedia Encyclopedic Reference",
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
                        en = f"{abstract}"
                        te = f"{abstract}"
                        hi = f"{abstract}"
                        return ToolResult(
                            success=True,
                            tool_name=self.name,
                            data={"abstract": abstract, "source": data.get("AbstractSource", "Web")},
                            spoken_summary={"english": en, "telugu": te, "hindi": hi},
                            source="DuckDuckGo Instant Answer",
                        )
        except Exception as e:
            logger.info("Search lookup timed out or failed (%s)", e)

        return ToolResult(
            success=False,
            tool_name=self.name,
            data={"query": clean_q},
            spoken_summary={
                "english": f"I checked for details regarding {clean_q}.",
                "telugu": f"{clean_q} గురించి వివరాలను పరిశీలించాను.",
                "hindi": f"{clean_q} के संदर्भ में जानकारी जाँची।",
            },
            source="Search Fallback",
        )
